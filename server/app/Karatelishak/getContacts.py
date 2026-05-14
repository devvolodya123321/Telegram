from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import UserResponse, user_to_response
from app.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.post("/getContacts", response_model=list[UserResponse])
async def get_contacts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contact.contact_user_id).where(Contact.user_id == user.id)
    )
    contact_ids = [row[0] for row in result.all()]
    if not contact_ids:
        return []
    users_result = await db.execute(select(User).where(User.id.in_(contact_ids)))
    return [user_to_response(u) for u in users_result.scalars()]
