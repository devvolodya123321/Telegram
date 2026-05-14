from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.sticker import StickerSet, UserStickerSet
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stickers", tags=["stickers"])


class CreateStickerSetRequest(BaseModel):
    name: str
    title: str
    is_animated: bool = False
    is_video: bool = False


class StickerSetResponse(BaseModel):
    id: int
    name: str
    title: str
    is_animated: bool
    is_video: bool
    stickers_count: int = 0


@router.post("/createStickerSet", response_model=StickerSetResponse)
async def create_sticker_set(
    body: CreateStickerSetRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(StickerSet).where(StickerSet.name == body.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="STICKER_SET_NAME_OCCUPIED")

    ss = StickerSet(
        name=body.name,
        title=body.title,
        creator_id=user.id,
        is_animated=body.is_animated,
        is_video=body.is_video,
    )
    db.add(ss)
    await db.flush()
    db.add(UserStickerSet(user_id=user.id, set_id=ss.id))
    await db.commit()

    return StickerSetResponse(
        id=ss.id, name=ss.name, title=ss.title,
        is_animated=ss.is_animated, is_video=ss.is_video,
    )
