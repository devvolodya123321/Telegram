from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.call import Call
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/calls", tags=["calls"])


class SetCallRatingRequest(BaseModel):
    call_id: int
    rating: int  # 1-5
    comment: Optional[str] = None


@router.post("/setCallRating")
async def set_call_rating(
    body: SetCallRatingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Call).where(Call.id == body.call_id))
    call = result.scalar_one_or_none()
    if call is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CALL_NOT_FOUND")
    if user.id not in (call.caller_id, call.callee_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CALL_ACCESS_DENIED")

    call.rating = max(1, min(5, body.rating))
    call.comment = body.comment
    await db.commit()
    return {"ok": True}
