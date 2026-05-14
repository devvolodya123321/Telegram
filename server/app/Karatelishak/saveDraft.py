import time
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.draft import Draft
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


class SaveDraftRequest(BaseModel):
    chat_id: int
    text: str
    reply_to_msg_id: Optional[int] = None


@router.post("/saveDraft")
async def save_draft(
    body: SaveDraftRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.user_id == user.id, Draft.chat_id == body.chat_id)
    )
    draft = result.scalar_one_or_none()
    if draft:
        draft.text = body.text
        draft.reply_to_msg_id = body.reply_to_msg_id
        draft.updated_at = int(time.time())
    else:
        draft = Draft(
            user_id=user.id,
            chat_id=body.chat_id,
            text=body.text,
            reply_to_msg_id=body.reply_to_msg_id,
        )
        db.add(draft)
    await db.commit()
    return {"ok": True}
