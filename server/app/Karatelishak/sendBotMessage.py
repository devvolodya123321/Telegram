from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids, update_dialog
from app.database import get_db
from app.models.bot import Bot
from app.models.message import Message
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/bots", tags=["bots"])


class SendBotMessageRequest(BaseModel):
    bot_id: int
    chat_id: int
    text: str


@router.post("/sendBotMessage")
async def send_bot_message(
    body: SendBotMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot).where(Bot.id == body.bot_id))
    bot = result.scalar_one_or_none()
    if bot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="BOT_NOT_FOUND")
    if bot.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="NOT_BOT_OWNER")

    msg = Message(
        chat_id=body.chat_id,
        from_id=user.id,
        text=f"[Bot:{bot.username}] {body.text}",
    )
    db.add(msg)
    await db.flush()

    member_ids = await get_chat_member_ids(db, body.chat_id)
    for uid in member_ids:
        await update_dialog(db, uid, body.chat_id, msg, increment_unread=(uid != user.id))
    await db.commit()
    return {"ok": True, "message_id": msg.id}
