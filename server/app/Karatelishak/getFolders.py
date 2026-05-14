from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.folder import ChatFolder, ChatFolderEntry
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.post("/getFolders")
async def get_folders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatFolder).where(ChatFolder.user_id == user.id).order_by(ChatFolder.position)
    )
    folders = result.scalars().all()

    response = []
    for f in folders:
        entries = await db.execute(
            select(ChatFolderEntry.chat_id).where(ChatFolderEntry.folder_id == f.id)
        )
        chat_ids = [row[0] for row in entries.all()]
        response.append({
            "id": f.id,
            "title": f.title,
            "chat_ids": chat_ids,
        })
    return {"folders": response}
