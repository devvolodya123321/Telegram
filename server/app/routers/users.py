"""
User profile endpoints.

  - POST /api/users/getUser
  - POST /api/users/getUsers
  - POST /api/users/updateProfile
  - POST /api/users/updateUsername
  - POST /api/users/getMe
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    phone: str
    first_name: str
    last_name: str
    username: Optional[str] = None
    bio: str = ""
    is_online: bool = False
    last_seen: int = 0

class GetUserRequest(BaseModel):
    user_id: int

class GetUsersRequest(BaseModel):
    user_ids: list[int]

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None

class UpdateUsernameRequest(BaseModel):
    username: str


def _user_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        phone=u.phone,
        first_name=u.first_name,
        last_name=u.last_name,
        username=u.username,
        bio=u.bio,
        is_online=updates_manager.is_online(u.id),
        last_seen=u.last_seen,
    )


@router.post("/getMe", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return _user_response(user)


@router.post("/getUser", response_model=UserResponse)
async def get_user(
    body: GetUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == body.user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="USER_NOT_FOUND")
    return _user_response(target)


@router.post("/getUsers", response_model=list[UserResponse])
async def get_users(
    body: GetUsersRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id.in_(body.user_ids)))
    return [_user_response(u) for u in result.scalars()]


@router.post("/updateProfile", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    if body.bio is not None:
        user.bio = body.bio
    await db.commit()
    return _user_response(user)


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
    return _user_response(user)
