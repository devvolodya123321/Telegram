from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.poll import Poll, PollOption, PollVote
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/polls", tags=["polls"])


class VotePollRequest(BaseModel):
    poll_id: int
    options: list[int]


@router.post("/votePoll")
async def vote_poll(
    body: VotePollRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Poll).where(Poll.id == body.poll_id))
    poll = result.scalar_one_or_none()
    if poll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="POLL_NOT_FOUND")
    if poll.is_closed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="POLL_CLOSED")

    await db.execute(
        delete(PollVote).where(PollVote.poll_id == body.poll_id, PollVote.user_id == user.id)
    )

    opts_result = await db.execute(
        select(PollOption).where(PollOption.poll_id == body.poll_id).order_by(PollOption.position)
    )
    options = opts_result.scalars().all()
    option_ids = [o.id for o in options]

    for idx in body.options:
        if 0 <= idx < len(option_ids):
            db.add(PollVote(poll_id=body.poll_id, option_id=option_ids[idx], user_id=user.id))

    await db.commit()
    return {"ok": True}
