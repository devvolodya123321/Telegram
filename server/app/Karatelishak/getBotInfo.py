from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bot import Bot, BotCommand
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/bots", tags=["bots"])


class GetBotInfoRequest(BaseModel):
    bot_id: int


@router.post("/getBotInfo")
async def get_bot_info(
    body: GetBotInfoRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot).where(Bot.id == body.bot_id))
    bot = result.scalar_one_or_none()
    if bot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="BOT_NOT_FOUND")

    cmds_result = await db.execute(select(BotCommand).where(BotCommand.bot_id == bot.id))
    commands = cmds_result.scalars().all()

    return {
        "id": bot.id,
        "name": bot.name,
        "username": bot.username,
        "description": bot.description,
        "commands": [
            {"command": c.command, "description": c.description} for c in commands
        ],
    }
