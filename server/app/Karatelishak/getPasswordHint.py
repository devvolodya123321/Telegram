from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/getPasswordHint")
async def get_password_hint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hint = getattr(user, "password_hint", None) or ""
    return {"hint": hint}
