from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import UserResponse, user_to_response
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class GetUsersRequest(BaseModel):
    user_ids: list[int]


@router.post("/getUsers", response_model=list[UserResponse])
async def get_users(
    body: GetUsersRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id.in_(body.user_ids)))
    return [user_to_response(u) for u in result.scalars()]
