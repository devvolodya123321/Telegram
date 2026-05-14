from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.draft import Draft
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


class GetDraftRequest(BaseModel):
    chat_id: int


@router.post("/getDraft")
async def get_draft(
    body: GetDraftRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.user_id == user.id, Draft.chat_id == body.chat_id)
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        return {"draft": None}
    return {
        "draft": {
            "text": draft.text,
            "reply_to_msg_id": draft.reply_to_msg_id,
            "updated_at": draft.updated_at,
        }
    }
