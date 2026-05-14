from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import PrivacySettings
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class PrivacyResponse(BaseModel):
    phone_visibility: str = "contacts"
    last_seen_visibility: str = "everyone"
    profile_photo_visibility: str = "everyone"
    forwards_visibility: str = "everyone"
    calls_visibility: str = "everyone"
    groups_visibility: str = "everyone"
    stories_visibility: str = "everyone"


@router.post("/getPrivacy", response_model=PrivacyResponse)
async def get_privacy(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrivacySettings).where(PrivacySettings.user_id == user.id)
    )
    ps = result.scalar_one_or_none()
    if ps is None:
        return PrivacyResponse()
    return PrivacyResponse(
        phone_visibility=ps.phone_visibility,
        last_seen_visibility=ps.last_seen_visibility,
        profile_photo_visibility=ps.profile_photo_visibility,
        forwards_visibility=ps.forwards_visibility,
        calls_visibility=ps.calls_visibility,
        groups_visibility=ps.groups_visibility,
        stories_visibility=ps.stories_visibility,
    )
