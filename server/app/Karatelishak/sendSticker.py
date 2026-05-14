from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, get_chat_member_ids, msg_to_response, update_dialog
from app.database import get_db
from app.models.message import Message
from app.models.sticker import Sticker
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stickers", tags=["stickers"])


class SendStickerRequest(BaseModel):
    chat_id: int
    sticker_id: int


@router.post("/sendSticker", response_model=MessageResponse)
async def send_sticker(
    body: SendStickerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    sticker_result = await db.execute(select(Sticker).where(Sticker.id == body.sticker_id))
    sticker = sticker_result.scalar_one_or_none()
    if sticker is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="STICKER_NOT_FOUND")

    msg = Message(
        chat_id=body.chat_id,
        from_id=user.id,
        text="",
        media_type="sticker",
        media_path=sticker.file_path,
    )
    db.add(msg)
    await db.flush()

    for uid in member_ids:
        await update_dialog(db, uid, body.chat_id, msg, increment_unread=(uid != user.id))
    await db.commit()

    resp = msg_to_response(msg)
    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id],
        {"type": "updateNewMessage", "message": resp.model_dump()},
    )
    return resp
