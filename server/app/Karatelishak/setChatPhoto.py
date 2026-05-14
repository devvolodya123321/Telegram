import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.message import Chat, ChatMember
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("/setChatPhoto")
async def set_chat_photo(
    chat_id: int = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user.id,
            ChatMember.role.in_(["owner", "admin"]),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_ADMIN_REQUIRED")

    chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CHAT_NOT_FOUND")

    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    content = await file.read()
    ext = os.path.splitext(file.filename or "photo")[1]
    stored_name = f"chat_{chat_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.MEDIA_DIR, stored_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    chat.photo_path = file_path
    await db.commit()
    return {"ok": True}
