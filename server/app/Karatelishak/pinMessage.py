from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Chat, ChatMember, Message
from app.models.user import User
from app.services.updates import updates_manager
from app.Karatelishak.helpers import get_chat_member_ids
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class PinMessageRequest(BaseModel):
    chat_id: int
    message_id: int


@router.post("/pinMessage")
async def pin_message(
    body: PinMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    admin_check = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == user.id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    if admin_check.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_MEMBER_REQUIRED")

    msg_result = await db.execute(
        select(Message).where(
            Message.id == body.message_id,
            Message.chat_id == body.chat_id,
        )
    )
    msg = msg_result.scalar_one_or_none()
    if msg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MESSAGE_NOT_FOUND")

    chat_result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat:
        chat.pinned_message_id = body.message_id
        await db.commit()

    member_ids = await get_chat_member_ids(db, body.chat_id)
    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id],
        {"type": "updatePinnedMessage", "chat_id": body.chat_id, "message_id": body.message_id},
    )
    return {"ok": True}
