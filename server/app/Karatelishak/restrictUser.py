from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin import AdminLog, ChatRestriction
from app.models.message import Chat
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


class RestrictUserRequest(BaseModel):
    chat_id: int
    user_id: int
    can_send_messages: bool = True
    can_send_media: bool = True


@router.post("/restrictUser")
async def restrict_user(
    body: RestrictUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")
    if chat.creator_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ADMIN_REQUIRED")

    existing = await db.execute(
        select(ChatRestriction).where(
            ChatRestriction.chat_id == body.chat_id,
            ChatRestriction.user_id == body.user_id,
        )
    )
    restriction = existing.scalar_one_or_none()
    if restriction:
        restriction.can_send_messages = body.can_send_messages
        restriction.can_send_media = body.can_send_media
    else:
        restriction = ChatRestriction(
            chat_id=body.chat_id, user_id=body.user_id,
            can_send_messages=body.can_send_messages,
            can_send_media=body.can_send_media,
        )
        db.add(restriction)

    db.add(AdminLog(
        chat_id=body.chat_id, admin_id=user.id,
        action="restrict_user", target_user_id=body.user_id,
        details=f"send_messages={body.can_send_messages}, send_media={body.can_send_media}",
    ))
    await db.commit()
    return {"ok": True}
