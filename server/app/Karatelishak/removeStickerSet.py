from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.sticker import UserStickerSet
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stickers", tags=["stickers"])


class RemoveStickerSetRequest(BaseModel):
    set_id: int


@router.post("/removeStickerSet")
async def remove_sticker_set(
    body: RemoveStickerSetRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(UserStickerSet).where(
            UserStickerSet.user_id == user.id,
            UserStickerSet.set_id == body.set_id,
        )
    )
    await db.commit()
    return {"ok": True}
