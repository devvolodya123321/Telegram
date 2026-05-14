from fastapi import APIRouter, Depends
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import BlockedUser, Contact
from app.models.message import ChatMember
from app.models.user import Session, User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/deleteAccount")
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Session).where(Session.user_id == user.id).values(is_active=False)
    )
    await db.execute(
        update(ChatMember).where(ChatMember.user_id == user.id).values(is_active=False)
    )
    await db.execute(delete(Contact).where(Contact.user_id == user.id))
    await db.execute(delete(BlockedUser).where(BlockedUser.user_id == user.id))
    await db.delete(user)
    await db.commit()
    return {"ok": True}
