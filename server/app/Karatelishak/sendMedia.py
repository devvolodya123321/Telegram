from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, get_chat_member_ids, msg_to_response, update_dialog
from app.database import get_db
from app.models.media import MediaFile
from app.models.message import Message
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/media", tags=["media"])


@router.post("/sendMedia", response_model=MessageResponse)
async def send_media(
    chat_id: int = Form(...),
    file_id: int = Form(...),
    text: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, chat_id)
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
        await update_dialog(db, uid, chat_id, msg, increment_unread=(uid != user.id))
    await db.commit()

    resp = msg_to_response(msg)
    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id],
        {"type": "updateNewMessage", "message": resp.model_dump()},
    )
    return resp
