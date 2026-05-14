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


class RequestCallRequest(BaseModel):
    user_id: int
    call_type: str = "voice"  # voice, video


class CallResponse(BaseModel):
    id: int
    caller_id: int
    callee_id: int
    call_type: str
    status: str
    created_at: int


@router.post("/requestCall", response_model=CallResponse)
async def request_call(
    body: RequestCallRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await db.execute(select(User).where(User.id == body.user_id))
    if target.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="USER_NOT_FOUND")

    call = Call(
        caller_id=user.id,
        callee_id=body.user_id,
        call_type=body.call_type,
        status="ringing",
    )
    db.add(call)
    await db.commit()

    await updates_manager.send_update(body.user_id, {
        "type": "updateIncomingCall",
        "call_id": call.id,
        "caller_id": user.id,
        "call_type": body.call_type,
    })

    return CallResponse(
        id=call.id,
        caller_id=call.caller_id,
        callee_id=call.callee_id,
        call_type=call.call_type,
        status=call.status,
        created_at=call.created_at,
    )
