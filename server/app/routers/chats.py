"""
Chat / group / channel management endpoints.

  - POST /api/chats/createChat         (group)
  - POST /api/chats/createChannel
  - POST /api/chats/editTitle
  - POST /api/chats/addUser
  - POST /api/chats/deleteUser
  - POST /api/chats/getFullChat
  - POST /api/chats/getMembers
  - POST /api/chats/leaveChat
  - POST /api/chats/startPrivate       (get or create 1-on-1 chat)
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class CreateChatRequest(BaseModel):
    title: str
    user_ids: list[int]

class CreateChannelRequest(BaseModel):
    title: str
    description: str = ""
    username: Optional[str] = None

class EditTitleRequest(BaseModel):
    chat_id: int
    title: str

class ChatUserRequest(BaseModel):
    chat_id: int
    user_id: int

class ChatIdRequest(BaseModel):
    chat_id: int

class StartPrivateRequest(BaseModel):
    user_id: int

class MemberInfo(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    role: str
    joined_at: int

class ChatInfo(BaseModel):
    id: int
    chat_type: str
    title: Optional[str] = None
    description: str = ""
    username: Optional[str] = None
    creator_id: Optional[int] = None
    members_count: int = 0
    created_at: int = 0


@router.post("/createChat", response_model=ChatInfo)
async def create_chat(
    body: CreateChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = Chat(
        chat_type="group",
        title=body.title,
        creator_id=user.id,
    )
    db.add(chat)
    await db.flush()

    db.add(ChatMember(chat_id=chat.id, user_id=user.id, role="owner"))
    for uid in body.user_ids:
        if uid != user.id:
            db.add(ChatMember(chat_id=chat.id, user_id=uid, role="member"))

    await db.commit()

    return ChatInfo(
        id=chat.id,
        chat_type=chat.chat_type,
        title=chat.title,
        creator_id=chat.creator_id,
        members_count=len(body.user_ids) + 1,
        created_at=chat.created_at,
    )


@router.post("/createChannel", response_model=ChatInfo)
async def create_channel(
    body: CreateChannelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = Chat(
        chat_type="channel",
        title=body.title,
        description=body.description,
        username=body.username,
        creator_id=user.id,
    )
    db.add(chat)
    await db.flush()
    db.add(ChatMember(chat_id=chat.id, user_id=user.id, role="owner"))
    await db.commit()

    return ChatInfo(
        id=chat.id,
        chat_type=chat.chat_type,
        title=chat.title,
        description=chat.description,
        username=chat.username,
        creator_id=chat.creator_id,
        members_count=1,
        created_at=chat.created_at,
    )


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


@router.post("/addUser")
async def add_user(
    body: ChatUserRequest,
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
        member.joined_at = int(time.time())
    else:
        db.add(ChatMember(chat_id=body.chat_id, user_id=body.user_id))

    await db.commit()

    await updates_manager.send_update(
        body.user_id,
        {"type": "updateChatParticipantAdd", "chat_id": body.chat_id, "user_id": body.user_id},
    )
    return {"ok": True}


@router.post("/deleteUser")
async def delete_user(
    body: ChatUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # must be admin/owner or removing self
    if body.user_id != user.id:
        admin_check = await db.execute(
            select(ChatMember).where(
                ChatMember.chat_id == body.chat_id,
                ChatMember.user_id == user.id,
                ChatMember.role.in_(["owner", "admin"]),
            )
        )
        if admin_check.scalar_one_or_none() is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_ADMIN_REQUIRED")

    result = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == body.user_id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USER_NOT_MEMBER")

    member.is_active = False
    await db.commit()
    return {"ok": True}


@router.post("/getFullChat", response_model=ChatInfo)
async def get_full_chat(
    body: ChatIdRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")

    count_result = await db.execute(
        select(func.count()).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    members_count = count_result.scalar() or 0

    return ChatInfo(
        id=chat.id,
        chat_type=chat.chat_type,
        title=chat.title,
        description=chat.description,
        username=chat.username,
        creator_id=chat.creator_id,
        members_count=members_count,
        created_at=chat.created_at,
    )


@router.post("/getMembers", response_model=list[MemberInfo])
async def get_members(
    body: ChatIdRequest,
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

    infos: list[MemberInfo] = []
    for m in members:
        user_result = await db.execute(select(User).where(User.id == m.user_id))
        u = user_result.scalar_one_or_none()
        if u:
            infos.append(
                MemberInfo(
                    user_id=u.id,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    role=m.role,
                    joined_at=m.joined_at,
                )
            )
    return infos


@router.post("/leaveChat")
async def leave_chat(
    body: ChatIdRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == body.chat_id,
            ChatMember.user_id == user.id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USER_NOT_MEMBER")
    member.is_active = False
    await db.commit()
    return {"ok": True}


@router.post("/startPrivate", response_model=ChatInfo)
async def start_private(
    body: StartPrivateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check if private chat already exists
    result = await db.execute(
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(Chat.chat_type == "private")
        .where(ChatMember.user_id.in_([user.id, body.user_id]))
        .group_by(Chat.id)
        .having(func.count(func.distinct(ChatMember.user_id)) == 2)
    )
    chat = result.scalar_one_or_none()
    if chat:
        return ChatInfo(
            id=chat.id,
            chat_type=chat.chat_type,
            members_count=2,
            created_at=chat.created_at,
        )

    chat = Chat(chat_type="private")
    db.add(chat)
    await db.flush()
    db.add(ChatMember(chat_id=chat.id, user_id=user.id, role="member"))
    db.add(ChatMember(chat_id=chat.id, user_id=body.user_id, role="member"))
    await db.commit()

    return ChatInfo(
        id=chat.id,
        chat_type=chat.chat_type,
        members_count=2,
        created_at=chat.created_at,
    )
