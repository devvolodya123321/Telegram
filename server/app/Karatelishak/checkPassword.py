from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.security import verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class CheckPasswordRequest(BaseModel):
    password: str


@router.post("/checkPassword")
async def check_password(
    body: CheckPasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.password_hash:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="PASSWORD_NOT_SET")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="PASSWORD_INVALID")
    return {"ok": True}
