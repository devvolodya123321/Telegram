from fastapi import APIRouter, Depends

from app.Karatelishak.helpers import UserResponse, user_to_response
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/getMe", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user_to_response(user)
