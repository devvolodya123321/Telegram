from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids
from app.database import get_db
from app.models.message import Message
from app.models.reaction import Reaction
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/reactions", tags=["reactions"])


class SendReactionRequest(BaseModel):
    chat_id: int
    message_id: int
    emoji: str  # empty string to remove


@router.post("/sendReaction")
async def send_reaction(
    body: SendReactionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_MEMBER_REQUIRED")

    msg_result = await db.execute(
        select(Message).where(Message.id == body.message_id, Message.chat_id == body.chat_id)
    )
    if msg_result.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MESSAGE_NOT_FOUND")

    await db.execute(
        delete(Reaction).where(
            Reaction.message_id == body.message_id,
            Reaction.user_id == user.id,
        )
    )

    if body.emoji:
        reaction = Reaction(
            message_id=body.message_id,
            chat_id=body.chat_id,
            user_id=user.id,
            emoji=body.emoji,
        )
        db.add(reaction)

    await db.commit()

    await updates_manager.broadcast_to_chat_members(
        [uid for uid in member_ids if uid != user.id],
        {
            "type": "updateMessageReaction",
            "chat_id": body.chat_id,
            "message_id": body.message_id,
            "user_id": user.id,
            "emoji": body.emoji,
        },
    )
    return {"ok": True}
