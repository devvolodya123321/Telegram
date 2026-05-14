from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import DialogResponse, MessageResponse, msg_to_response
from app.database import get_db
from app.models.message import Chat, ChatMember, Dialog, Message
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class GetDialogsRequest(BaseModel):
    offset: int = 0
    limit: int = 50


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

    response: list[DialogResponse] = []
    for d in dialogs:
        chat_result = await db.execute(select(Chat).where(Chat.id == d.chat_id))
        chat = chat_result.scalar_one_or_none()
        if chat is None:
            continue

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
                u = await db.execute(select(User).where(User.id == other_id))
                other_user = u.scalar_one_or_none()
                if other_user:
                    title = f"{other_user.first_name} {other_user.last_name}".strip()

        top_msg: Optional[MessageResponse] = None
        if d.top_message_id:
            msg_result = await db.execute(select(Message).where(Message.id == d.top_message_id))
            msg = msg_result.scalar_one_or_none()
            if msg:
                top_msg = msg_to_response(msg)

        response.append(DialogResponse(
            chat_id=d.chat_id,
            chat_type=chat.chat_type,
            title=title,
            unread_count=d.unread_count,
            top_message=top_msg,
        ))
    return response
