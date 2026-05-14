from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class GetMembersRequest(BaseModel):
    chat_id: int


class MemberInfo(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    role: str
    joined_at: int


@router.post("/getMembers", response_model=list[MemberInfo])
async def get_members(
    body: GetMembersRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    members = result.scalars().all()

    member_list: list[MemberInfo] = []
    for m in members:
        u_result = await db.execute(select(User).where(User.id == m.user_id))
        u = u_result.scalar_one_or_none()
        if u:
            member_list.append(MemberInfo(
                user_id=u.id,
                first_name=u.first_name,
                last_name=u.last_name,
                role=m.role,
                joined_at=m.joined_at,
            ))
    return member_list
