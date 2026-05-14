from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.topic import Topic
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/topics", tags=["topics"])


class GetTopicsRequest(BaseModel):
    chat_id: int


@router.post("/getTopics")
async def get_topics(
    body: GetTopicsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Topic).where(Topic.chat_id == body.chat_id).order_by(Topic.created_at)
    )
    topics = result.scalars().all()
    return {
        "topics": [
            {
                "id": t.id,
                "title": t.title,
                "icon_emoji": t.icon_emoji,
                "creator_id": t.creator_id,
                "is_closed": t.is_closed,
                "created_at": t.created_at,
            }
            for t in topics
        ]
    }
