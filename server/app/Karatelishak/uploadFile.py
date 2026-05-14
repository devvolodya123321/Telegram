import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.media import MediaFile
from app.models.user import User
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
