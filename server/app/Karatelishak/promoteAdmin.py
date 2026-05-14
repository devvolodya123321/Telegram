from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin import AdminLog
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PromoteAdminRequest(BaseModel):
    chat_id: int
    user_id: int


@router.post("/promoteAdmin")
async def promote_admin(
    body: PromoteAdminRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")
    if chat.creator_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ADMIN_REQUIRED")

    member_result = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == body.user_id,
        )
    )
    member = member_result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USER_NOT_MEMBER")

    member.role = "admin"

    db.add(AdminLog(
        chat_id=body.chat_id, admin_id=user.id,
        action="promote_admin", target_user_id=body.user_id,
    ))
    await db.commit()
    return {"ok": True}
