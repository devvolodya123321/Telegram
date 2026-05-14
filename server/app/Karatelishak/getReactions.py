from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.reaction import Reaction
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/reactions", tags=["reactions"])


class GetReactionsRequest(BaseModel):
    chat_id: int
    message_id: int


class ReactionInfo(BaseModel):
    user_id: int
    emoji: str
    created_at: int


@router.post("/getReactions", response_model=list[ReactionInfo])
async def get_reactions(
    body: GetReactionsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reaction).where(
            Reaction.message_id == body.message_id,
            Reaction.chat_id == body.chat_id,
        )
    )
    return [
        ReactionInfo(user_id=r.user_id, emoji=r.emoji, created_at=r.created_at)
        for r in result.scalars()
    ]
