import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import NotificationSettings
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class MuteChatRequest(BaseModel):
    chat_id: int
    mute_until: int = 0  # 0 = forever


@router.post("/muteChat")
async def mute_chat(
    body: MuteChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationSettings).where(
            NotificationSettings.user_id == user.id,
            NotificationSettings.chat_id == body.chat_id,
        )
    )
    ns = result.scalar_one_or_none()
    if ns is None:
        ns = NotificationSettings(user_id=user.id, chat_id=body.chat_id)
        db.add(ns)

    ns.muted = True
    ns.mute_until = body.mute_until if body.mute_until > 0 else None
    await db.commit()
    return {"ok": True}
