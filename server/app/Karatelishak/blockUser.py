from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import BlockedUser
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class BlockUserRequest(BaseModel):
    user_id: int


@router.post("/block")
async def block_user(
    body: BlockUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(BlockedUser).where(
            BlockedUser.user_id == user.id,
            BlockedUser.blocked_user_id == body.user_id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(BlockedUser(user_id=user.id, blocked_user_id=body.user_id))
        await db.commit()
    return {"ok": True}
