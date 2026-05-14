from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids
from app.database import get_db
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/activity", tags=["activity"])


class SetTypingRequest(BaseModel):
    chat_id: int
    action: str = "typing"


@router.post("/setTyping")
async def set_typing(
    body: SetTypingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    for uid in member_ids:
        if uid != user.id:
            await updates_manager.send_update(
                uid,
                {"type": "typing", "chat_id": body.chat_id, "user_id": user.id, "action": body.action},
            )
    return {"ok": True}
