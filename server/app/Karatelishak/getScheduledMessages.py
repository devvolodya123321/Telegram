from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scheduled import ScheduledMessage
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/scheduled", tags=["scheduled"])


class GetScheduledMessagesRequest(BaseModel):
    chat_id: int


@router.post("/getScheduledMessages")
async def get_scheduled_messages(
    body: GetScheduledMessagesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScheduledMessage).where(
            ScheduledMessage.chat_id == body.chat_id,
            ScheduledMessage.from_id == user.id,
            ScheduledMessage.is_sent == False,  # noqa: E712
        ).order_by(ScheduledMessage.send_at)
    )
    messages = result.scalars().all()
    return {
        "messages": [
            {
                "id": m.id,
                "text": m.text,
                "send_at": m.send_at,
                "created_at": m.created_at,
            }
            for m in messages
        ]
    }
