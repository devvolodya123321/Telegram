from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import UserResponse, user_to_response
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class UpdateUsernameRequest(BaseModel):
    username: str


@router.post("/updateUsername", response_model=UserResponse)
async def update_username(
    body: UpdateUsernameRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where(User.username == body.username, User.id != user.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USERNAME_OCCUPIED")
    user.username = body.username
    await db.commit()
    return user_to_response(user)
