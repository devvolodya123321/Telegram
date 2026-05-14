from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import UserResponse, user_to_response
from app.database import get_db
from app.models.contact import BlockedUser
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class GetBlockedRequest(BaseModel):
    offset: int = 0
    limit: int = 50


@router.post("/getBlocked", response_model=list[UserResponse])
async def get_blocked(
    body: GetBlockedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BlockedUser.blocked_user_id)
        .where(BlockedUser.user_id == user.id)
        .offset(body.offset)
        .limit(body.limit)
    )
    blocked_ids = [row[0] for row in result.all()]
    if not blocked_ids:
        return []
    users_result = await db.execute(select(User).where(User.id.in_(blocked_ids)))
    return [user_to_response(u) for u in users_result.scalars()]
