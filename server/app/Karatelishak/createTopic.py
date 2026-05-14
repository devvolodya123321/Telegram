from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids
from app.database import get_db
from app.models.topic import Topic
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/topics", tags=["topics"])


class CreateTopicRequest(BaseModel):
    chat_id: int
    title: str
    icon_emoji: Optional[str] = None


@router.post("/createTopic")
async def create_topic(
    body: CreateTopicRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    topic = Topic(
        chat_id=body.chat_id,
        title=body.title,
        icon_emoji=body.icon_emoji,
        creator_id=user.id,
    )
    db.add(topic)
    await db.commit()
    return {"ok": True, "topic_id": topic.id}
