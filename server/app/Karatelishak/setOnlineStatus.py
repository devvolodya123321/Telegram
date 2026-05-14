import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/activity", tags=["activity"])


class SetOnlineStatusRequest(BaseModel):
    online: bool = True


@router.post("/setOnlineStatus")
async def set_online_status(
    body: SetOnlineStatusRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.is_online = body.online
    if not body.online:
        user.last_seen = int(time.time())
    await db.commit()
    return {"ok": True, "online": user.is_online}
