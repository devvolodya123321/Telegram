import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.story import Story
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stories", tags=["stories"])


class GetStoriesRequest(BaseModel):
    user_id: int


class StoryInfo(BaseModel):
    id: int
    user_id: int
    media_type: str
    media_url: str
    caption: str
    views_count: int
    is_pinned: bool
    expires_at: int
    created_at: int


@router.post("/getStories", response_model=list[StoryInfo])
async def get_stories(
    body: GetStoriesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = int(time.time())
    result = await db.execute(
        select(Story).where(
            Story.user_id == body.user_id,
            Story.is_deleted == False,  # noqa: E712
            Story.expires_at > now,
        ).order_by(Story.created_at.desc())
    )
    stories = result.scalars().all()
    return [
        StoryInfo(
            id=s.id,
            user_id=s.user_id,
            media_type=s.media_type,
            media_url=f"/api/media/download/{s.id}",
            caption=s.caption,
            views_count=s.views_count,
            is_pinned=s.is_pinned,
            expires_at=s.expires_at,
            created_at=s.created_at,
        )
        for s in stories
    ]
