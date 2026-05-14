import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bot import Bot
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/bots", tags=["bots"])


class RegisterBotRequest(BaseModel):
    name: str
    username: str


@router.post("/registerBot")
async def register_bot(
    body: RegisterBotRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Bot).where(Bot.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="BOT_USERNAME_OCCUPIED")

    bot = Bot(
        owner_id=user.id,
        name=body.name,
        username=body.username,
        token=secrets.token_hex(32),
    )
    db.add(bot)
    await db.commit()
    return {"ok": True, "bot_id": bot.id, "token": bot.token}
