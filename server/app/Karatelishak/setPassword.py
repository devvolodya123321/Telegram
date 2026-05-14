from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.security import hash_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SetPasswordRequest(BaseModel):
    new_password: str


@router.post("/setPassword")
async def set_password(
    body: SetPasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"ok": True}
