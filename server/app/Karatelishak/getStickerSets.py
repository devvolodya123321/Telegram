from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.sticker import Sticker, StickerSet, UserStickerSet
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stickers", tags=["stickers"])


class StickerSetInfo(BaseModel):
    id: int
    name: str
    title: str
    is_animated: bool
    is_video: bool
    stickers_count: int


class StickerInfo(BaseModel):
    id: int
    emoji: str
    file_url: str
    width: int
    height: int


@router.post("/getStickerSets")
async def get_sticker_sets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserStickerSet.set_id).where(UserStickerSet.user_id == user.id)
    )
    set_ids = [row[0] for row in result.all()]
    if not set_ids:
        return {"sets": []}

    sets: list[dict] = []
    for sid in set_ids:
        ss_result = await db.execute(select(StickerSet).where(StickerSet.id == sid))
        ss = ss_result.scalar_one_or_none()
        if ss is None:
            continue

        count_result = await db.execute(
            select(func.count()).select_from(Sticker).where(Sticker.set_id == sid)
        )
        count = count_result.scalar() or 0

        stickers_result = await db.execute(
            select(Sticker).where(Sticker.set_id == sid).order_by(Sticker.position)
        )
        stickers = [
            StickerInfo(
                id=s.id,
                emoji=s.emoji,
                file_url=f"/api/media/download/{s.id}",
                width=s.width,
                height=s.height,
            )
            for s in stickers_result.scalars()
        ]

        sets.append({
            "id": ss.id,
            "name": ss.name,
            "title": ss.title,
            "is_animated": ss.is_animated,
            "is_video": ss.is_video,
            "stickers_count": count,
            "stickers": [s.model_dump() for s in stickers],
        })

    return {"sets": sets}
