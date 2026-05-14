import random
import secrets

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import AuthCode

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SendCodeRequest(BaseModel):
    phone: str


class SendCodeResponse(BaseModel):
    phone_code_hash: str
    code_length: int = 5
    debug_code: str | None = None


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

    return SendCodeResponse(
        phone_code_hash=phone_code_hash,
        debug_code=code,
    )
