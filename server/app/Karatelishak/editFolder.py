from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.folder import ChatFolder, ChatFolderEntry
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/folders", tags=["folders"])


class EditFolderRequest(BaseModel):
    folder_id: int
    title: Optional[str] = None
    chat_ids: Optional[list[int]] = None


@router.post("/editFolder")
async def edit_folder(
    body: EditFolderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatFolder).where(ChatFolder.id == body.folder_id, ChatFolder.user_id == user.id)
    )
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FOLDER_NOT_FOUND")

    if body.title is not None:
        folder.title = body.title
    if body.chat_ids is not None:
        await db.execute(delete(ChatFolderEntry).where(ChatFolderEntry.folder_id == folder.id))
        for cid in body.chat_ids:
            db.add(ChatFolderEntry(folder_id=folder.id, chat_id=cid))
    await db.commit()
    return {"ok": True}
