from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.story import Story, StoryView
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stories", tags=["stories"])


class ViewStoryRequest(BaseModel):
    story_id: int


@router.post("/viewStory")
async def view_story(
    body: ViewStoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Story).where(Story.id == body.story_id))
    story = result.scalar_one_or_none()
    if story is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="STORY_NOT_FOUND")

    existing = await db.execute(
        select(StoryView).where(
            StoryView.story_id == body.story_id,
            StoryView.viewer_id == user.id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(StoryView(story_id=body.story_id, viewer_id=user.id))
        story.views_count += 1
        await db.commit()

    return {"ok": True}
