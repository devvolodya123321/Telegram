from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import NotificationSettings
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class SetNotificationSettingsRequest(BaseModel):
    chat_id: Optional[int] = None
    muted: Optional[bool] = None
    mute_until: Optional[int] = None
    sound: Optional[str] = None
    show_previews: Optional[bool] = None


@router.post("/setNotificationSettings")
async def set_notification_settings(
    body: SetNotificationSettingsRequest,
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

    if body.muted is not None:
        ns.muted = body.muted
    if body.mute_until is not None:
        ns.mute_until = body.mute_until
    if body.sound is not None:
        ns.sound = body.sound
    if body.show_previews is not None:
        ns.show_previews = body.show_previews

    await db.commit()
    return {"ok": True}
