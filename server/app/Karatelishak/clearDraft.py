from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.draft import Draft
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


class ClearDraftRequest(BaseModel):
    chat_id: int


@router.post("/clearDraft")
async def clear_draft(
    body: ClearDraftRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(Draft).where(Draft.user_id == user.id, Draft.chat_id == body.chat_id)
    )
    await db.commit()
    return {"ok": True}
