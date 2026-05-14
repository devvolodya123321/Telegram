from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import NotificationSettings
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class UnmuteChatRequest(BaseModel):
    chat_id: int


@router.post("/unmuteChat")
async def unmute_chat(
    body: UnmuteChatRequest,
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
    if ns:
        ns.muted = False
        ns.mute_until = None
        await db.commit()
    return {"ok": True}
