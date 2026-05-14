import os
import time
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.notification import ProfilePhoto
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/setProfilePhoto")
async def set_profile_photo(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    content = await file.read()
    ext = os.path.splitext(file.filename or "photo")[1]
    stored_name = f"avatar_{user.id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.MEDIA_DIR, stored_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    await db.execute(
        update(ProfilePhoto)
        .where(ProfilePhoto.user_id == user.id, ProfilePhoto.is_current == True)  # noqa: E712
        .values(is_current=False)
    )

    photo = ProfilePhoto(
        user_id=user.id,
        file_path=file_path,
        is_current=True,
        uploaded_at=int(time.time()),
    )
    db.add(photo)
    user.photo_path = file_path
    await db.commit()

    return {"ok": True, "photo_id": photo.id}
