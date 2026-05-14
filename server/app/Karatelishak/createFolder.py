from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.folder import ChatFolder, ChatFolderEntry
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/folders", tags=["folders"])


class CreateFolderRequest(BaseModel):
    title: str
    chat_ids: list[int] = []


@router.post("/createFolder")
async def create_folder(
    body: CreateFolderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = ChatFolder(user_id=user.id, title=body.title)
    db.add(folder)
    await db.flush()
    for cid in body.chat_ids:
        db.add(ChatFolderEntry(folder_id=folder.id, chat_id=cid))
    await db.commit()
    return {"ok": True, "folder_id": folder.id}
