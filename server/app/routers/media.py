"""
Media upload / download endpoints.

  - POST /api/media/upload
  - GET  /api/media/download/{file_id}
  - POST /api/messages/sendMedia   (send message with attachment)
"""

import os
import time
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.media import MediaFile
from app.models.message import ChatMember, Dialog, Message
from app.models.user import User
from app.routers.messages import MessageResponse, _get_chat_member_ids, _msg_to_response, _update_dialog
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/media", tags=["media"])


class UploadResponse(BaseModel):
    file_id: int
    file_name: str
    file_size: int
    mime_type: str


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="FILE_TOO_LARGE",
        )

    ext = os.path.splitext(file.filename or "file")[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.MEDIA_DIR, stored_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    mime = file.content_type or "application/octet-stream"
    media_type = "document"
    if mime.startswith("image/"):
        media_type = "photo"
    elif mime.startswith("video/"):
        media_type = "video"
    elif mime.startswith("audio/"):
        media_type = "audio"

    media = MediaFile(
        uploader_id=user.id,
        file_name=file.filename or stored_name,
        file_path=file_path,
        file_size=len(content),
        mime_type=mime,
        media_type=media_type,
    )
    db.add(media)
    await db.commit()

    return UploadResponse(
        file_id=media.id,
        file_name=media.file_name,
        file_size=media.file_size,
        mime_type=media.mime_type,
    )


@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MediaFile).where(MediaFile.id == file_id))
    media = result.scalar_one_or_none()
    if media is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FILE_NOT_FOUND")

    if not os.path.exists(media.file_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FILE_MISSING")

    return FileResponse(
        media.file_path,
        media_type=media.mime_type,
        filename=media.file_name,
    )


@router.post("/sendMedia", response_model=MessageResponse)
async def send_media(
    chat_id: int = Form(...),
    file_id: int = Form(...),
    text: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await _get_chat_member_ids(db, chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    media_result = await db.execute(select(MediaFile).where(MediaFile.id == file_id))
    media = media_result.scalar_one_or_none()
    if media is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="FILE_NOT_FOUND")

    msg = Message(
        chat_id=chat_id,
        from_id=user.id,
        text=text,
        media_type=media.media_type,
        media_path=f"/api/media/download/{media.id}",
    )
    db.add(msg)
    await db.flush()

    for uid in member_ids:
        await _update_dialog(db, uid, chat_id, msg, increment_unread=(uid != user.id))
    await db.commit()

    resp = _msg_to_response(msg)
    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id],
        {"type": "updateNewMessage", "message": resp.model_dump()},
    )
    return resp
