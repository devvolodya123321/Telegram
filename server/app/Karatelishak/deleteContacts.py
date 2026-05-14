from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class DeleteContactsRequest(BaseModel):
    user_id: int


@router.post("/deleteContacts")
async def delete_contacts(
    body: DeleteContactsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contact).where(
            Contact.user_id == user.id,
            Contact.contact_user_id == body.user_id,
        )
    )
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return {"ok": True}
