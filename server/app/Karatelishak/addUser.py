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


class AddUserRequest(BaseModel):
    chat_id: int
    user_id: int


@router.post("/addUser")
async def add_user(
    body: AddUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_check = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == user.id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    if member_check.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_MEMBER_REQUIRED")

    existing = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == body.user_id,
        )
    )
    member = existing.scalar_one_or_none()
    if member:
        if member.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USER_ALREADY_MEMBER")
        member.is_active = True
    else:
        db.add(ChatMember(chat_id=body.chat_id, user_id=body.user_id, role="member"))
    await db.commit()

    await updates_manager.send_update(body.user_id, {
        "type": "updateChatUserAdded",
        "chat_id": body.chat_id,
        "user_id": body.user_id,
        "inviter_id": user.id,
    })
    return {"ok": True}
