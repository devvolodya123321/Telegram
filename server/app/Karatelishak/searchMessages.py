from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, msg_to_response
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class SearchMessagesRequest(BaseModel):
    chat_id: Optional[int] = None
    query: str
    offset: int = 0
    limit: int = 50


@router.post("/search", response_model=list[MessageResponse])
async def search_messages(
    body: SearchMessagesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Message)
        .where(
            Message.text.ilike(f"%{body.query}%"),
            Message.is_deleted == False,  # noqa: E712
        )
        .order_by(Message.id.desc())
        .offset(body.offset)
        .limit(body.limit)
    )
    if body.chat_id is not None:
        q = q.where(Message.chat_id == body.chat_id)
    result = await db.execute(q)
    return [msg_to_response(m) for m in result.scalars()]
