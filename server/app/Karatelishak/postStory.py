import os
import time
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.story import Story
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.post("/postStory")
async def post_story(
    file: UploadFile = File(...),
    caption: str = Form(""),
    privacy: str = Form("everyone"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    content = await file.read()
    ext = os.path.splitext(file.filename or "story")[1]
    stored_name = f"story_{user.id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.MEDIA_DIR, stored_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    mime = file.content_type or ""
    media_type = "video" if mime.startswith("video/") else "photo"

    story = Story(
        user_id=user.id,
        media_type=media_type,
        media_path=file_path,
        caption=caption,
        privacy=privacy,
    )
    db.add(story)
    await db.commit()

    return {
        "ok": True,
        "story_id": story.id,
        "expires_at": story.expires_at,
    }
