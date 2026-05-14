from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.folder import ChatFolder, ChatFolderEntry
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/folders", tags=["folders"])


class DeleteFolderRequest(BaseModel):
    folder_id: int


@router.post("/deleteFolder")
async def delete_folder(
    body: DeleteFolderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatFolder).where(ChatFolder.id == body.folder_id, ChatFolder.user_id == user.id)
    )
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FOLDER_NOT_FOUND")

    await db.execute(delete(ChatFolderEntry).where(ChatFolderEntry.folder_id == folder.id))
    await db.delete(folder)
    await db.commit()
    return {"ok": True}
