"""
Messaging endpoints — mirrors Telegram's messages.* methods.

Supported:
  - POST   /api/messages/sendMessage
  - POST   /api/messages/getHistory
  - POST   /api/messages/getDialogs
  - POST   /api/messages/readHistory
  - POST   /api/messages/deleteMessages
  - POST   /api/messages/editMessage
  - POST   /api/messages/forwardMessages
  - POST   /api/messages/search
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Chat, ChatMember, Dialog, Message
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


# ── Schemas ───────────────────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    chat_id: int
    text: str
    reply_to_msg_id: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    from_id: int
    text: str
    media_type: Optional[str] = None
    media_path: Optional[str] = None
    reply_to_msg_id: Optional[int] = None
    is_edited: bool = False
    date: int

class GetHistoryRequest(BaseModel):
    chat_id: int
    offset_id: int = 0
    limit: int = 50

class GetDialogsRequest(BaseModel):
    offset: int = 0
    limit: int = 50

class DialogResponse(BaseModel):
    chat_id: int
    chat_type: str
    title: Optional[str] = None
    unread_count: int
    top_message: Optional[MessageResponse] = None

class ReadHistoryRequest(BaseModel):
    chat_id: int
    max_id: int

class DeleteMessagesRequest(BaseModel):
    chat_id: int
    message_ids: list[int]

class EditMessageRequest(BaseModel):
    chat_id: int
    message_id: int
    text: str

class ForwardMessagesRequest(BaseModel):
    from_chat_id: int
    to_chat_id: int
    message_ids: list[int]

class SearchRequest(BaseModel):
    chat_id: Optional[int] = None
    query: str
    offset: int = 0
    limit: int = 50


# ── Helpers ───────────────────────────────────────────────────────────────

def _msg_to_response(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        chat_id=msg.chat_id,
        from_id=msg.from_id,
        text=msg.text,
        media_type=msg.media_type,
        media_path=msg.media_path,
        reply_to_msg_id=msg.reply_to_msg_id,
        is_edited=msg.is_edited,
        date=msg.date,
    )


async def _ensure_private_chat(
    db: AsyncSession, user_id: int, peer_id: int
) -> Chat:
    """Return or create the private chat between two users."""
    result = await db.execute(
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(Chat.chat_type == "private")
        .where(
            ChatMember.user_id.in_([user_id, peer_id]),
        )
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


async def _get_chat_member_ids(db: AsyncSession, chat_id: int) -> list[int]:
    result = await db.execute(
        select(ChatMember.user_id).where(
            ChatMember.chat_id == chat_id,
            ChatMember.is_active == True,  # noqa: E712
        )
    )
    return [row[0] for row in result.all()]


async def _update_dialog(
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


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/sendMessage", response_model=MessageResponse)
async def send_message(
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await _get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    msg = Message(
        chat_id=body.chat_id,
        from_id=user.id,
        text=body.text,
        reply_to_msg_id=body.reply_to_msg_id,
    )
    db.add(msg)
    await db.flush()

    for uid in member_ids:
        await _update_dialog(db, uid, body.chat_id, msg, increment_unread=(uid != user.id))

    await db.commit()

    resp = _msg_to_response(msg)
    update_payload = {
        "type": "updateNewMessage",
        "message": resp.model_dump(),
    }
    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id], update_payload
    )
    return resp


@router.post("/getHistory", response_model=list[MessageResponse])
async def get_history(
    body: GetHistoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await _get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_READ_FORBIDDEN")

    query = (
        select(Message)
        .where(Message.chat_id == body.chat_id, Message.is_deleted == False)  # noqa: E712
    )
    if body.offset_id > 0:
        query = query.where(Message.id < body.offset_id)
    query = query.order_by(Message.id.desc()).limit(body.limit)

    result = await db.execute(query)
    return [_msg_to_response(m) for m in result.scalars()]


@router.post("/getDialogs", response_model=list[DialogResponse])
async def get_dialogs(
    body: GetDialogsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dialog)
        .where(Dialog.user_id == user.id)
        .order_by(Dialog.top_message_id.desc())
        .offset(body.offset)
        .limit(body.limit)
    )
    dialogs = result.scalars().all()

    responses: list[DialogResponse] = []
    for d in dialogs:
        chat_result = await db.execute(select(Chat).where(Chat.id == d.chat_id))
        chat = chat_result.scalar_one_or_none()
        if chat is None:
            continue

        top_message = None
        if d.top_message_id:
            msg_result = await db.execute(
                select(Message).where(Message.id == d.top_message_id)
            )
            msg = msg_result.scalar_one_or_none()
            if msg:
                top_message = _msg_to_response(msg)

        title = chat.title
        if chat.chat_type == "private":
            other = await db.execute(
                select(ChatMember.user_id).where(
                    ChatMember.chat_id == chat.id,
                    ChatMember.user_id != user.id,
                )
            )
            other_id = other.scalar_one_or_none()
            if other_id:
                other_user_result = await db.execute(
                    select(User).where(User.id == other_id)
                )
                other_user = other_user_result.scalar_one_or_none()
                if other_user:
                    title = f"{other_user.first_name} {other_user.last_name}".strip()

        responses.append(
            DialogResponse(
                chat_id=d.chat_id,
                chat_type=chat.chat_type,
                title=title,
                unread_count=d.unread_count,
                top_message=top_message,
            )
        )
    return responses


@router.post("/readHistory")
async def read_history(
    body: ReadHistoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Dialog)
        .where(Dialog.user_id == user.id, Dialog.chat_id == body.chat_id)
        .values(unread_count=0, last_read_inbox_id=body.max_id)
    )
    await db.commit()

    member_ids = await _get_chat_member_ids(db, body.chat_id)
    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id],
        {
            "type": "updateReadHistoryOutbox",
            "chat_id": body.chat_id,
            "max_id": body.max_id,
            "user_id": user.id,
        },
    )
    return {"ok": True}


@router.post("/deleteMessages")
async def delete_messages(
    body: DeleteMessagesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Message)
        .where(
            Message.chat_id == body.chat_id,
            Message.id.in_(body.message_ids),
            Message.from_id == user.id,
        )
        .values(is_deleted=True)
    )
    await db.commit()

    member_ids = await _get_chat_member_ids(db, body.chat_id)
    await updates_manager.broadcast_to_chat_members(
        member_ids,
        {
            "type": "updateDeleteMessages",
            "chat_id": body.chat_id,
            "message_ids": body.message_ids,
        },
    )
    return {"ok": True}


@router.post("/editMessage", response_model=MessageResponse)
async def edit_message(
    body: EditMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message).where(
            Message.id == body.message_id,
            Message.chat_id == body.chat_id,
            Message.from_id == user.id,
            Message.is_deleted == False,  # noqa: E712
        )
    )
    msg = result.scalar_one_or_none()
    if msg is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="MESSAGE_NOT_FOUND")

    msg.text = body.text
    msg.is_edited = True
    msg.edit_date = int(time.time())
    await db.commit()

    resp = _msg_to_response(msg)
    member_ids = await _get_chat_member_ids(db, body.chat_id)
    await updates_manager.broadcast_to_chat_members(
        member_ids,
        {"type": "updateEditMessage", "message": resp.model_dump()},
    )
    return resp


@router.post("/forwardMessages", response_model=list[MessageResponse])
async def forward_messages(
    body: ForwardMessagesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    to_member_ids = await _get_chat_member_ids(db, body.to_chat_id)
    if user.id not in to_member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    result = await db.execute(
        select(Message).where(
            Message.chat_id == body.from_chat_id,
            Message.id.in_(body.message_ids),
            Message.is_deleted == False,  # noqa: E712
        )
    )
    originals = result.scalars().all()

    forwarded: list[MessageResponse] = []
    for orig in originals:
        fwd = Message(
            chat_id=body.to_chat_id,
            from_id=user.id,
            text=orig.text,
            media_type=orig.media_type,
            media_path=orig.media_path,
            forward_from_id=orig.from_id,
            forward_from_msg_id=orig.id,
        )
        db.add(fwd)
        await db.flush()

        for uid in to_member_ids:
            await _update_dialog(db, uid, body.to_chat_id, fwd, increment_unread=(uid != user.id))
        forwarded.append(_msg_to_response(fwd))

    await db.commit()

    for resp in forwarded:
        await updates_manager.broadcast_to_chat_members(
            [uid for uid in to_member_ids if uid != user.id],
            {"type": "updateNewMessage", "message": resp.model_dump()},
        )
    return forwarded


@router.post("/search", response_model=list[MessageResponse])
async def search_messages(
    body: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Message).where(
        Message.is_deleted == False,  # noqa: E712
        Message.text.ilike(f"%{body.query}%"),
    )
    if body.chat_id:
        member_ids = await _get_chat_member_ids(db, body.chat_id)
        if user.id not in member_ids:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_READ_FORBIDDEN")
        query = query.where(Message.chat_id == body.chat_id)
    else:
        user_chats = await db.execute(
            select(ChatMember.chat_id).where(ChatMember.user_id == user.id)
        )
        chat_ids = [row[0] for row in user_chats.all()]
        query = query.where(Message.chat_id.in_(chat_ids))

    query = query.order_by(Message.id.desc()).offset(body.offset).limit(body.limit)
    result = await db.execute(query)
    return [_msg_to_response(m) for m in result.scalars()]
