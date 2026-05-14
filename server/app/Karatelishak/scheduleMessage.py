from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids
from app.database import get_db
from app.models.scheduled import ScheduledMessage
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/scheduled", tags=["scheduled"])


class ScheduleMessageRequest(BaseModel):
    chat_id: int
    text: str
    send_at: int


@router.post("/scheduleMessage")
async def schedule_message(
    body: ScheduleMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    sm = ScheduledMessage(
        chat_id=body.chat_id,
        from_id=user.id,
        text=body.text,
        send_at=body.send_at,
    )
    db.add(sm)
    await db.commit()
    return {"ok": True, "message_id": sm.id, "send_at": sm.send_at}
