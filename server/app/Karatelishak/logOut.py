from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Session, User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/logOut")
async def log_out(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Session)
        .where(Session.user_id == user.id, Session.is_active == True)  # noqa: E712
        .values(is_active=False)
    )
    await db.commit()
    return {"ok": True}
