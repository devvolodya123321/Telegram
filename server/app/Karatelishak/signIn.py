import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import AuthCode, Session, User
from app.utils.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignInRequest(BaseModel):
    phone: str
    phone_code_hash: str
    code: str


class AuthResult(BaseModel):
    user_id: int
    auth_token: str
    first_name: str
    last_name: str
    phone: str
    is_new_user: bool = False


@router.post("/signIn", response_model=AuthResult)
async def sign_in(body: SignInRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuthCode).where(
            AuthCode.phone == body.phone,
            AuthCode.phone_code_hash == body.phone_code_hash,
            AuthCode.used == False,  # noqa: E712
        )
    )
    auth_code = result.scalar_one_or_none()
    if auth_code is None or auth_code.code != body.code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="PHONE_CODE_INVALID")
    if time.time() - auth_code.created_at > 300:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="PHONE_CODE_EXPIRED")

    auth_code.used = True

    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="PHONE_NUMBER_UNOCCUPIED")

    token = create_access_token({"user_id": user.id, "phone": user.phone})
    session = Session(user_id=user.id, auth_token=token)
    db.add(session)
    await db.commit()

    return AuthResult(
        user_id=user.id,
        auth_token=token,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
    )
