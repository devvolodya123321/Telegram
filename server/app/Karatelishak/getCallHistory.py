from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.call import Call
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/calls", tags=["calls"])


class GetCallHistoryRequest(BaseModel):
    offset: int = 0
    limit: int = 50


class CallHistoryItem(BaseModel):
    id: int
    caller_id: int
    callee_id: int
    call_type: str
    status: str
    duration: int
    created_at: int


@router.post("/getCallHistory", response_model=list[CallHistoryItem])
async def get_call_history(
    body: GetCallHistoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Call)
        .where(or_(Call.caller_id == user.id, Call.callee_id == user.id))
        .order_by(Call.created_at.desc())
        .offset(body.offset)
        .limit(body.limit)
    )
    calls = result.scalars().all()
    return [
        CallHistoryItem(
            id=c.id,
            caller_id=c.caller_id,
            callee_id=c.callee_id,
            call_type=c.call_type,
            status=c.status,
            duration=c.duration,
            created_at=c.created_at,
        )
        for c in calls
    ]
