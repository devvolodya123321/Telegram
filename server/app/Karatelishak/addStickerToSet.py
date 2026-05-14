import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.sticker import Sticker, StickerSet
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/stickers", tags=["stickers"])


@router.post("/addStickerToSet")
async def add_sticker_to_set(
    set_id: int = Form(...),
    emoji: str = Form(""),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ss_result = await db.execute(select(StickerSet).where(StickerSet.id == set_id))
    ss = ss_result.scalar_one_or_none()
    if ss is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="STICKER_SET_NOT_FOUND")
    if ss.creator_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="NOT_STICKER_SET_OWNER")

    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    content = await file.read()
    ext = os.path.splitext(file.filename or "sticker")[1]
    stored_name = f"sticker_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.MEDIA_DIR, stored_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    count_result = await db.execute(
        select(func.count()).select_from(Sticker).where(Sticker.set_id == set_id)
    )
    position = (count_result.scalar() or 0) + 1

    sticker = Sticker(
        set_id=set_id,
        emoji=emoji,
        file_path=file_path,
        file_size=len(content),
        position=position,
    )
    db.add(sticker)
    await db.commit()
    return {"ok": True, "sticker_id": sticker.id}
