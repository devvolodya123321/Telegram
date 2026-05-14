from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import ProfilePhoto
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class GetProfilePhotosRequest(BaseModel):
    user_id: int


class PhotoResponse(BaseModel):
    id: int
    file_url: str
    is_current: bool
    uploaded_at: int


@router.post("/getProfilePhotos", response_model=list[PhotoResponse])
async def get_profile_photos(
    body: GetProfilePhotosRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfilePhoto)
        .where(ProfilePhoto.user_id == body.user_id)
        .order_by(ProfilePhoto.uploaded_at.desc())
    )
    photos = result.scalars().all()
    return [
        PhotoResponse(
            id=p.id,
            file_url=f"/api/media/download/{p.id}",
            is_current=p.is_current,
            uploaded_at=p.uploaded_at,
        )
        for p in photos
    ]
