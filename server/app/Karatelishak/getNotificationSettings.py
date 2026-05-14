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


class GetNotificationSettingsRequest(BaseModel):
    chat_id: Optional[int] = None


class NotificationSettingsResponse(BaseModel):
    muted: bool = False
    mute_until: Optional[int] = None
    sound: str = "default"
    show_previews: bool = True


@router.post("/getNotificationSettings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    body: GetNotificationSettingsRequest,
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
        return NotificationSettingsResponse()
    return NotificationSettingsResponse(
        muted=ns.muted,
        mute_until=ns.mute_until,
        sound=ns.sound or "default",
        show_previews=ns.show_previews,
    )
