from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import BlockedUser
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class UnblockUserRequest(BaseModel):
    user_id: int


@router.post("/unblock")
async def unblock_user(
    body: UnblockUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BlockedUser).where(
            BlockedUser.user_id == user.id,
            BlockedUser.blocked_user_id == body.user_id,
        )
    )
    blocked = result.scalar_one_or_none()
    if blocked:
        await db.delete(blocked)
        await db.commit()
    return {"ok": True}
