from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, get_chat_member_ids, msg_to_response, update_dialog
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class SendMessageRequest(BaseModel):
    chat_id: int
    text: str
    reply_to_msg_id: Optional[int] = None


@router.post("/sendMessage", response_model=MessageResponse)
async def send_message(
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    msg = Message(
        chat_id=body.chat_id,
        from_id=user.id,
        text=body.text,
        reply_to_msg_id=body.reply_to_msg_id,
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
