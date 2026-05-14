from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.poll import Poll
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/polls", tags=["polls"])


class ClosePollRequest(BaseModel):
    poll_id: int


@router.post("/closePoll")
async def close_poll(
    body: ClosePollRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Poll).where(Poll.id == body.poll_id))
    poll = result.scalar_one_or_none()
    if poll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="POLL_NOT_FOUND")
    if poll.creator_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="NOT_POLL_CREATOR")

    poll.is_closed = True
    await db.commit()
    return {"ok": True}
