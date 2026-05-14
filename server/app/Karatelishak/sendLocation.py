from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids, msg_to_response, update_dialog
from app.database import get_db
from app.models.geo import LocationMessage
from app.models.message import Message
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/geo", tags=["geo"])


class SendLocationRequest(BaseModel):
    chat_id: int
    latitude: float
    longitude: float


@router.post("/sendLocation")
async def send_location(
    body: SendLocationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    msg = Message(
        chat_id=body.chat_id,
        from_id=user.id,
        text=f"[Location] {body.latitude},{body.longitude}",
        media_type="location",
    )
    db.add(msg)
    await db.flush()

    loc = LocationMessage(
        message_id=msg.id, chat_id=body.chat_id, from_id=user.id,
        latitude=body.latitude, longitude=body.longitude,
    )
    db.add(loc)

    for uid in member_ids:
        await update_dialog(db, uid, body.chat_id, msg, increment_unread=(uid != user.id))
    await db.commit()
    return {"ok": True, "message_id": msg.id}
