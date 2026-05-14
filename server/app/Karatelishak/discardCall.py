import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.call import Call
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/calls", tags=["calls"])


class DiscardCallRequest(BaseModel):
    call_id: int
    reason: str = "hangup"  # hangup, missed, declined, busy


@router.post("/discardCall")
async def discard_call(
    body: DiscardCallRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Call).where(Call.id == body.call_id))
    call = result.scalar_one_or_none()
    if call is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CALL_NOT_FOUND")
    if user.id not in (call.caller_id, call.callee_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CALL_ACCESS_DENIED")

    now = int(time.time())
    if call.status == "active" and call.started_at:
        call.duration = now - call.started_at
        call.status = "ended"
    elif call.status == "ringing":
        call.status = body.reason if body.reason in ("missed", "declined", "busy") else "ended"
    else:
        call.status = "ended"
    call.ended_at = now
    await db.commit()

    other_id = call.callee_id if user.id == call.caller_id else call.caller_id
    await updates_manager.send_update(other_id, {
        "type": "updateCallDiscarded",
        "call_id": call.id,
        "reason": body.reason,
    })
    return {"ok": True}
