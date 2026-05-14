from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, get_chat_member_ids, msg_to_response
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class GetHistoryRequest(BaseModel):
    chat_id: int
    offset_id: int = 0
    limit: int = 50


@router.post("/getHistory", response_model=list[MessageResponse])
async def get_history(
    body: GetHistoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_READ_FORBIDDEN")

    query = (
        select(Message)
        .where(
            Message.chat_id == body.chat_id,
            Message.is_deleted == False,  # noqa: E712
        )
        .order_by(Message.id.desc())
        .limit(body.limit)
    )
    if body.offset_id > 0:
        query = query.where(Message.id < body.offset_id)

    result = await db.execute(query)
    return [msg_to_response(m) for m in result.scalars()]
