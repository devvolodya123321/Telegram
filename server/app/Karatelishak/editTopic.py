from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.topic import Topic
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/topics", tags=["topics"])


class EditTopicRequest(BaseModel):
    topic_id: int
    title: str


@router.post("/editTopic")
async def edit_topic(
    body: EditTopicRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Topic).where(Topic.id == body.topic_id))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="TOPIC_NOT_FOUND")

    topic.title = body.title
    await db.commit()
    return {"ok": True}
