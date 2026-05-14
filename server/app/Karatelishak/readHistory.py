from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Dialog
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class ReadHistoryRequest(BaseModel):
    chat_id: int
    max_id: int


@router.post("/readHistory")
async def read_history(
    body: ReadHistoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dialog).where(Dialog.user_id == user.id, Dialog.chat_id == body.chat_id)
    )
    dialog = result.scalar_one_or_none()
    if dialog:
        dialog.unread_count = 0
        dialog.last_read_inbox_id = body.max_id
        await db.commit()
    return {"ok": True}
