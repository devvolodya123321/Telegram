from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.story import Story
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stories", tags=["stories"])


class DeleteStoryRequest(BaseModel):
    story_id: int


@router.post("/deleteStory")
async def delete_story(
    body: DeleteStoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Story).where(Story.id == body.story_id, Story.user_id == user.id)
    )
    story = result.scalar_one_or_none()
    if story is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="STORY_NOT_FOUND")

    story.is_deleted = True
    await db.commit()
    return {"ok": True}
