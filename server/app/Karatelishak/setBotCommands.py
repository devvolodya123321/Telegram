from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bot import Bot, BotCommand
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/bots", tags=["bots"])


class CommandItem(BaseModel):
    command: str
    description: str = ""


class SetBotCommandsRequest(BaseModel):
    bot_id: int
    commands: list[CommandItem]


@router.post("/setBotCommands")
async def set_bot_commands(
    body: SetBotCommandsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot).where(Bot.id == body.bot_id))
    bot = result.scalar_one_or_none()
    if bot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="BOT_NOT_FOUND")
    if bot.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="NOT_BOT_OWNER")

    await db.execute(delete(BotCommand).where(BotCommand.bot_id == bot.id))
    for cmd in body.commands:
        db.add(BotCommand(bot_id=bot.id, command=cmd.command, description=cmd.description))
    await db.commit()
    return {"ok": True}
