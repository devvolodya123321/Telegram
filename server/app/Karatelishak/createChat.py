from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import ChatInfo
from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class CreateChatRequest(BaseModel):
    title: str
    user_ids: list[int]


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
