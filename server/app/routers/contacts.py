"""
Contacts endpoints — mirrors Telegram's contacts.* methods.

  - POST /api/contacts/importContacts
  - POST /api/contacts/getContacts
  - POST /api/contacts/search
  - POST /api/contacts/deleteContacts
  - POST /api/contacts/block
  - POST /api/contacts/unblock
  - POST /api/contacts/getBlocked
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import BlockedUser, Contact
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class UserInfo(BaseModel):
    id: int
    phone: str
    first_name: str
    last_name: str
    username: Optional[str] = None
    bio: str = ""
    is_online: bool = False
    last_seen: int = 0


class ImportContactItem(BaseModel):
    phone: str
    first_name: str
    last_name: str = ""

class ImportContactsRequest(BaseModel):
    contacts: list[ImportContactItem]

class SearchRequest(BaseModel):
    query: str
    limit: int = 20

class UserIdRequest(BaseModel):
    user_id: int

class GetBlockedRequest(BaseModel):
    offset: int = 0
    limit: int = 50


def _user_to_info(u: User) -> UserInfo:
    return UserInfo(
        id=u.id,
        phone=u.phone,
        first_name=u.first_name,
        last_name=u.last_name,
        username=u.username,
        bio=u.bio,
        is_online=u.is_online,
        last_seen=u.last_seen,
    )


@router.post("/importContacts", response_model=list[UserInfo])
async def import_contacts(
    body: ImportContactsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    phones = [c.phone for c in body.contacts]
    result = await db.execute(select(User).where(User.phone.in_(phones)))
    found_users = result.scalars().all()

    imported: list[UserInfo] = []
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
            # Check if mutual
            reverse = await db.execute(
                select(Contact).where(
                    Contact.user_id == fu.id,
                    Contact.contact_user_id == user.id,
                )
            )
            if reverse.scalar_one_or_none() is not None:
                await db.execute(
                    select(Contact)
                    .where(Contact.user_id == fu.id, Contact.contact_user_id == user.id)
                )
                # update mutual flags below after flush
        imported.append(_user_to_info(fu))

    await db.commit()
    return imported


@router.post("/getContacts", response_model=list[UserInfo])
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
    return [_user_to_info(u) for u in users_result.scalars()]


@router.post("/search", response_model=list[UserInfo])
async def search_contacts(
    body: SearchRequest,
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
    return [_user_to_info(u) for u in result.scalars()]


@router.post("/deleteContacts")
async def delete_contacts(
    body: UserIdRequest,
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


@router.post("/block")
async def block_user(
    body: UserIdRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(BlockedUser).where(
            BlockedUser.user_id == user.id,
            BlockedUser.blocked_user_id == body.user_id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(BlockedUser(user_id=user.id, blocked_user_id=body.user_id))
        await db.commit()
    return {"ok": True}


@router.post("/unblock")
async def unblock_user(
    body: UserIdRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BlockedUser).where(
            BlockedUser.user_id == user.id,
            BlockedUser.blocked_user_id == body.user_id,
        )
    )
    blocked = result.scalar_one_or_none()
    if blocked:
        await db.delete(blocked)
        await db.commit()
    return {"ok": True}


@router.post("/getBlocked", response_model=list[UserInfo])
async def get_blocked(
    body: GetBlockedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BlockedUser.blocked_user_id)
        .where(BlockedUser.user_id == user.id)
        .offset(body.offset)
        .limit(body.limit)
    )
    blocked_ids = [row[0] for row in result.all()]
    if not blocked_ids:
        return []
    users_result = await db.execute(select(User).where(User.id.in_(blocked_ids)))
    return [_user_to_info(u) for u in users_result.scalars()]
