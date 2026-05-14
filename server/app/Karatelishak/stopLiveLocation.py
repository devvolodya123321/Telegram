from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.geo import LocationMessage
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/geo", tags=["geo"])


class StopLiveLocationRequest(BaseModel):
    message_id: int


@router.post("/stopLiveLocation")
async def stop_live_location(
    body: StopLiveLocationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LocationMessage).where(
            LocationMessage.message_id == body.message_id,
            LocationMessage.from_id == user.id,
            LocationMessage.is_live == True,  # noqa: E712
        )
    )
    loc = result.scalar_one_or_none()
    if loc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="LIVE_LOCATION_NOT_FOUND")

    loc.is_stopped = True
    await db.commit()
    return {"ok": True}
