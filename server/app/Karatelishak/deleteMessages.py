from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class DeleteMessagesRequest(BaseModel):
    chat_id: int
    message_ids: list[int]


@router.post("/deleteMessages")
async def delete_messages(
    body: DeleteMessagesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_MEMBER_REQUIRED")

    await db.execute(
        update(Message)
        .where(
            Message.id.in_(body.message_ids),
            Message.chat_id == body.chat_id,
        )
        .values(is_deleted=True)
    )
    await db.commit()
    return {"ok": True, "deleted_count": len(body.message_ids)}
