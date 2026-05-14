from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import PrivacySettings
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class SetPrivacyRequest(BaseModel):
    phone_visibility: Optional[str] = None
    last_seen_visibility: Optional[str] = None
    profile_photo_visibility: Optional[str] = None
    forwards_visibility: Optional[str] = None
    calls_visibility: Optional[str] = None
    groups_visibility: Optional[str] = None
    stories_visibility: Optional[str] = None


@router.post("/setPrivacy")
async def set_privacy(
    body: SetPrivacyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrivacySettings).where(PrivacySettings.user_id == user.id)
    )
    ps = result.scalar_one_or_none()
    if ps is None:
        ps = PrivacySettings(user_id=user.id)
        db.add(ps)

    for field in [
        "phone_visibility", "last_seen_visibility", "profile_photo_visibility",
        "forwards_visibility", "calls_visibility", "groups_visibility", "stories_visibility",
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(ps, field, val)

    await db.commit()
    return {"ok": True}
