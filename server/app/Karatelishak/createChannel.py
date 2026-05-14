from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import ChatInfo
from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class CreateChannelRequest(BaseModel):
    title: str
    description: str = ""
    username: Optional[str] = None


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
