"""Shared helpers used across multiple Karatelishak handlers."""

import time
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Chat, ChatMember, Dialog, Message
from app.models.user import User
from app.services.updates import updates_manager


# ── Common response schemas ──────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    from_id: int
    text: str
    media_type: Optional[str] = None
    media_path: Optional[str] = None
    reply_to_msg_id: Optional[int] = None
    forward_from_id: Optional[int] = None
    forward_from_msg_id: Optional[int] = None
    is_edited: bool = False
    date: int


class UserResponse(BaseModel):
    id: int
    phone: str
    first_name: str
    last_name: str
    username: Optional[str] = None
    bio: str = ""
    photo_url: Optional[str] = None
    is_online: bool = False
    last_seen: int = 0


class ChatInfo(BaseModel):
    id: int
    chat_type: str
    title: Optional[str] = None
    description: str = ""
    username: Optional[str] = None
    photo_url: Optional[str] = None
    creator_id: Optional[int] = None
    members_count: int = 0
    created_at: int = 0


class DialogResponse(BaseModel):
    chat_id: int
    chat_type: str
    title: Optional[str] = None
    unread_count: int
    top_message: Optional[MessageResponse] = None


# ── Helper functions ─────────────────────────────────────────────────────

def msg_to_response(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        chat_id=msg.chat_id,
        from_id=msg.from_id,
        text=msg.text,
        media_type=msg.media_type,
        media_path=msg.media_path,
        reply_to_msg_id=msg.reply_to_msg_id,
        forward_from_id=msg.forward_from_id,
        forward_from_msg_id=msg.forward_from_msg_id,
        is_edited=msg.is_edited,
        date=msg.date,
    )


def user_to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        phone=u.phone,
        first_name=u.first_name,
        last_name=u.last_name,
        username=u.username,
        bio=u.bio,
        photo_url=f"/api/media/download/{u.photo_path}" if u.photo_path else None,
        is_online=updates_manager.is_online(u.id),
        last_seen=u.last_seen,
    )


async def get_chat_member_ids(db: AsyncSession, chat_id: int) -> list[int]:
    result = await db.execute(
        select(ChatMember.user_id).where(
            ChatMember.chat_id == chat_id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    return [row[0] for row in result.all()]


async def ensure_private_chat(db: AsyncSession, user_id: int, peer_id: int) -> Chat:
    result = await db.execute(
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(Chat.chat_type == "private")
        .where(ChatMember.user_id.in_([user_id, peer_id]))
        .group_by(Chat.id)
        .having(func.count(func.distinct(ChatMember.user_id)) == 2)
    )
    chat = result.scalar_one_or_none()
    if chat:
        return chat

    chat = Chat(chat_type="private")
    db.add(chat)
    await db.flush()
    db.add(ChatMember(chat_id=chat.id, user_id=user_id, role="member"))
    db.add(ChatMember(chat_id=chat.id, user_id=peer_id, role="member"))
    await db.flush()
    return chat


async def update_dialog(
    db: AsyncSession, user_id: int, chat_id: int, message: Message, *, increment_unread: bool
) -> None:
    result = await db.execute(
        select(Dialog).where(Dialog.user_id == user_id, Dialog.chat_id == chat_id)
    )
    dialog = result.scalar_one_or_none()
    if dialog is None:
        dialog = Dialog(
            user_id=user_id,
            chat_id=chat_id,
            top_message_id=message.id,
            unread_count=1 if increment_unread else 0,
        )
        db.add(dialog)
    else:
        dialog.top_message_id = message.id
        if increment_unread:
            dialog.unread_count += 1
