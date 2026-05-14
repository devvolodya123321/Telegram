import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.media import MediaFile
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MediaFile).where(MediaFile.id == file_id))
    media = result.scalar_one_or_none()
    if media is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FILE_NOT_FOUND")

    if not os.path.exists(media.file_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FILE_MISSING")

    return FileResponse(
        media.file_path,
        media_type=media.mime_type,
        filename=media.file_name,
    )
