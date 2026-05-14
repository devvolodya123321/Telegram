"""
Authentication endpoints — mirrors Telegram's auth.* methods.

Supported flow:
  1. POST /api/auth/sendCode        -> sends SMS code (stub)
  2. POST /api/auth/signIn          -> verify code, get token
  3. POST /api/auth/signUp          -> register new user
  4. POST /api/auth/logOut           -> invalidate session
  5. POST /api/auth/checkPassword   -> 2FA password check
"""

import random
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import AuthCode, Session, User
from app.utils.auth import get_current_user
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request / response schemas ───────────────────────────────────────────

class SendCodeRequest(BaseModel):
    phone: str

class SendCodeResponse(BaseModel):
    phone_code_hash: str
    code_length: int = 5
    # In stub mode the code itself is returned for testing convenience
    debug_code: str | None = None

class SignInRequest(BaseModel):
    phone: str
    phone_code_hash: str
    code: str

class SignUpRequest(BaseModel):
    phone: str
    phone_code_hash: str
    code: str
    first_name: str
    last_name: str = ""

class AuthResult(BaseModel):
    user_id: int
    auth_token: str
    first_name: str
    last_name: str
    phone: str
    is_new_user: bool = False

class CheckPasswordRequest(BaseModel):
    password: str

class SetPasswordRequest(BaseModel):
    new_password: str


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/sendCode", response_model=SendCodeResponse)
async def send_code(body: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    code = f"{random.randint(10000, 99999)}"
    phone_code_hash = secrets.token_hex(16)

    auth_code = AuthCode(
        phone=body.phone,
        code=code,
        phone_code_hash=phone_code_hash,
    )
    db.add(auth_code)
    await db.commit()

    # In production replace with a real SMS provider
    return SendCodeResponse(
        phone_code_hash=phone_code_hash,
        debug_code=code,
    )


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


@router.post("/signUp", response_model=AuthResult)
async def sign_up(body: SignUpRequest, db: AsyncSession = Depends(get_db)):
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

    auth_code.used = True

    existing = await db.execute(select(User).where(User.phone == body.phone))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="PHONE_NUMBER_OCCUPIED")

    user = User(
        phone=body.phone,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    db.add(user)
    await db.flush()

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
        is_new_user=True,
    )


@router.post("/logOut")
async def log_out(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.user_id == user.id, Session.is_active == True)  # noqa: E712
    )
    for session in result.scalars():
        session.is_active = False
    await db.commit()
    return {"ok": True}


@router.post("/setPassword")
async def set_password(
    body: SetPasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"ok": True}


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
