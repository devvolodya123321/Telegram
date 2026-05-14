from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class JoinChatRequest(BaseModel):
    chat_id: int


@router.post("/joinChat")
async def join_chat(
    body: JoinChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")

    existing = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == user.id,
        )
    )
    member = existing.scalar_one_or_none()
    if member:
        if member.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USER_ALREADY_MEMBER")
        member.is_active = True
    else:
        db.add(ChatMember(chat_id=body.chat_id, user_id=user.id, role="member"))
    await db.commit()
    return {"ok": True}
