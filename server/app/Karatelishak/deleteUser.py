from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import ChatMember
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class DeleteUserRequest(BaseModel):
    chat_id: int
    user_id: int


@router.post("/deleteUser")
async def delete_user(
    body: DeleteUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    admin_check = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == user.id,
            ChatMember.role.in_(["owner", "admin"]),
        )
    )
    if admin_check.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_ADMIN_REQUIRED")

    target = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == body.user_id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    member = target.scalar_one_or_none()
    if member is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USER_NOT_MEMBER")

    member.is_active = False
    await db.commit()

    await updates_manager.send_update(body.user_id, {
        "type": "updateChatUserDeleted",
        "chat_id": body.chat_id,
        "user_id": body.user_id,
    })
    return {"ok": True}
