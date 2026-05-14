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


class AcceptCallRequest(BaseModel):
    call_id: int


@router.post("/acceptCall")
async def accept_call(
    body: AcceptCallRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Call).where(Call.id == body.call_id))
    call = result.scalar_one_or_none()
    if call is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CALL_NOT_FOUND")
    if call.callee_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CALL_NOT_FOR_YOU")
    if call.status != "ringing":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="CALL_ALREADY_HANDLED")

    call.status = "active"
    call.started_at = int(time.time())
    await db.commit()

    await updates_manager.send_update(call.caller_id, {
        "type": "updateCallAccepted",
        "call_id": call.id,
    })
    return {"ok": True, "call_id": call.id}
