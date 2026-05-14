from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, msg_to_response
from app.database import get_db
from app.models.message import Chat, Message
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class GetPinnedMessagesRequest(BaseModel):
    chat_id: int


@router.post("/getPinnedMessages", response_model=list[MessageResponse])
async def get_pinned_messages(
    body: GetPinnedMessagesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_result = await db.execute(select(Chat).where(Chat.id == body.chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")

    if chat.pinned_message_id is None:
        return []

    msg_result = await db.execute(select(Message).where(Message.id == chat.pinned_message_id))
    msg = msg_result.scalar_one_or_none()
    if msg is None:
        return []
    return [msg_to_response(msg)]
