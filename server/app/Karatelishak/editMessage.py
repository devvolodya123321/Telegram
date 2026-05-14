import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, get_chat_member_ids, msg_to_response
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class EditMessageRequest(BaseModel):
    chat_id: int
    message_id: int
    text: str


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
        )
    )
    msg = result.scalar_one_or_none()
    if msg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MESSAGE_NOT_FOUND")

    msg.text = body.text
    msg.is_edited = True
    msg.edit_date = int(time.time())
    await db.commit()

    resp = msg_to_response(msg)
    member_ids = await get_chat_member_ids(db, body.chat_id)
    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id],
        {"type": "updateEditMessage", "message": resp.model_dump()},
    )
    return resp
