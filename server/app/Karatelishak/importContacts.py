from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import UserResponse, user_to_response
from app.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class ImportContactItem(BaseModel):
    phone: str
    first_name: str
    last_name: str = ""


class ImportContactsRequest(BaseModel):
    contacts: list[ImportContactItem]


@router.post("/importContacts", response_model=list[UserResponse])
async def import_contacts(
    body: ImportContactsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    phones = [c.phone for c in body.contacts]
    result = await db.execute(select(User).where(User.phone.in_(phones)))
    found_users = result.scalars().all()

    imported: list[UserResponse] = []
    for fu in found_users:
        if fu.id == user.id:
            continue
        existing = await db.execute(
            select(Contact).where(
                Contact.user_id == user.id,
                Contact.contact_user_id == fu.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(Contact(user_id=user.id, contact_user_id=fu.id))
        imported.append(user_to_response(fu))

    await db.commit()
    return imported
