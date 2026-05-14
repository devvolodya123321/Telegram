from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import ProfilePhoto
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class DeleteProfilePhotoRequest(BaseModel):
    photo_id: int


@router.post("/deleteProfilePhoto")
async def delete_profile_photo(
    body: DeleteProfilePhotoRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfilePhoto).where(
            ProfilePhoto.id == body.photo_id,
            ProfilePhoto.user_id == user.id,
        )
    )
    photo = result.scalar_one_or_none()
    if photo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PHOTO_NOT_FOUND")

    was_current = photo.is_current
    await db.delete(photo)

    if was_current:
        prev = await db.execute(
            select(ProfilePhoto)
            .where(ProfilePhoto.user_id == user.id)
            .order_by(ProfilePhoto.uploaded_at.desc())
            .limit(1)
        )
        prev_photo = prev.scalar_one_or_none()
        if prev_photo:
            prev_photo.is_current = True
            user.photo_path = prev_photo.file_path
        else:
            user.photo_path = None

    await db.commit()
    return {"ok": True}
