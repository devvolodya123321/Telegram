from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import ChatInfo
from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class GetFullChatRequest(BaseModel):
    chat_id: int


@router.post("/getFullChat", response_model=ChatInfo)
async def get_full_chat(
    body: GetFullChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")

    count_result = await db.execute(
        select(func.count())
        .select_from(ChatMember)
        .where(ChatMember.chat_id == chat.id, ChatMember.is_active == True)  # noqa: E712
    )
    members_count = count_result.scalar() or 0

    return ChatInfo(
        id=chat.id,
        chat_type=chat.chat_type,
        title=chat.title,
        description=chat.description,
        username=chat.username,
        photo_url=f"/api/media/download/{chat.photo_path}" if chat.photo_path else None,
        creator_id=chat.creator_id,
        members_count=members_count,
        created_at=chat.created_at,
    )
