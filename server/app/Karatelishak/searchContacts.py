from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import UserResponse, user_to_response
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class SearchContactsRequest(BaseModel):
    query: str
    limit: int = 20


@router.post("/search", response_model=list[UserResponse])
async def search_contacts(
    body: SearchContactsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).where(
        User.id != user.id,
        (
            User.username.ilike(f"%{body.query}%")
            | User.first_name.ilike(f"%{body.query}%")
            | User.last_name.ilike(f"%{body.query}%")
            | User.phone.ilike(f"%{body.query}%")
        ),
    ).limit(body.limit)
    result = await db.execute(query)
    return [user_to_response(u) for u in result.scalars()]
