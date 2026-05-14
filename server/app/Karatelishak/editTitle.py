from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class EditTitleRequest(BaseModel):
    chat_id: int
    title: str


@router.post("/editTitle")
async def edit_title(
    body: EditTitleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == user.id,
            ChatMember.role.in_(["owner", "admin"]),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_ADMIN_REQUIRED")

    chat_result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")

    chat.title = body.title
    await db.commit()
    return {"ok": True}
