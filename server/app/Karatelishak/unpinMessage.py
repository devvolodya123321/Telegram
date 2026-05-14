from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class UnpinMessageRequest(BaseModel):
    chat_id: int


@router.post("/unpinMessage")
async def unpin_message(
    body: UnpinMessageRequest,
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

    chat_result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat:
        chat.pinned_message_id = None
        await db.commit()
    return {"ok": True}
