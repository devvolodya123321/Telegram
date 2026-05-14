from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.poll import Poll, PollOption, PollVote
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/polls", tags=["polls"])


class GetPollResultsRequest(BaseModel):
    poll_id: int


@router.post("/getPollResults")
async def get_poll_results(
    body: GetPollResultsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Poll).where(Poll.id == body.poll_id))
    poll = result.scalar_one_or_none()
    if poll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="POLL_NOT_FOUND")

    opts_result = await db.execute(
        select(PollOption).where(PollOption.poll_id == body.poll_id).order_by(PollOption.position)
    )
    options = opts_result.scalars().all()

    results = []
    for opt in options:
        count_result = await db.execute(
            select(func.count()).select_from(PollVote).where(PollVote.option_id == opt.id)
        )
        count = count_result.scalar() or 0
        results.append({"option": opt.text, "votes": count})

    total_result = await db.execute(
        select(func.count(func.distinct(PollVote.user_id))).select_from(PollVote).where(PollVote.poll_id == body.poll_id)
    )
    total_voters = total_result.scalar() or 0

    return {
        "poll_id": poll.id,
        "question": poll.question,
        "is_closed": poll.is_closed,
        "total_voters": total_voters,
        "results": results,
    }
