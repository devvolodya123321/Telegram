from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import ChatInfo, ensure_private_chat
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["chats"])


class StartPrivateRequest(BaseModel):
    user_id: int


@router.post("/startPrivate", response_model=ChatInfo)
async def start_private(
    body: StartPrivateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await db.execute(select(User).where(User.id == body.user_id))
    if target.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="USER_NOT_FOUND")

    chat = await ensure_private_chat(db, user.id, body.user_id)
    await db.commit()

    return ChatInfo(
        id=chat.id,
        chat_type=chat.chat_type,
        members_count=2,
        created_at=chat.created_at,
    )
