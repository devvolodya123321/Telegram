from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scheduled import ScheduledMessage
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/scheduled", tags=["scheduled"])


class DeleteScheduledMessageRequest(BaseModel):
    message_id: int


@router.post("/deleteScheduledMessage")
async def delete_scheduled_message(
    body: DeleteScheduledMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScheduledMessage).where(
            ScheduledMessage.id == body.message_id,
            ScheduledMessage.from_id == user.id,
        )
    )
    sm = result.scalar_one_or_none()
    if sm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MESSAGE_NOT_FOUND")

    await db.delete(sm)
    await db.commit()
    return {"ok": True}
