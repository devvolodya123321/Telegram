from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, get_chat_member_ids, msg_to_response, update_dialog
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


class ForwardMessagesRequest(BaseModel):
    from_chat_id: int
    to_chat_id: int
    message_ids: list[int]


@router.post("/forwardMessages", response_model=list[MessageResponse])
async def forward_messages(
    body: ForwardMessagesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    to_member_ids = await get_chat_member_ids(db, body.to_chat_id)
    if user.id not in to_member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    result = await db.execute(
        select(Message).where(
            Message.id.in_(body.message_ids),
            Message.chat_id == body.from_chat_id,
        )
    )
    original_msgs = result.scalars().all()

    forwarded: list[MessageResponse] = []
    for orig in original_msgs:
        new_msg = Message(
            chat_id=body.to_chat_id,
            from_id=user.id,
            text=orig.text,
            media_type=orig.media_type,
            media_path=orig.media_path,
            forward_from_id=orig.from_id,
            forward_from_msg_id=orig.id,
        )
        db.add(new_msg)
        await db.flush()

        for uid in to_member_ids:
            await update_dialog(db, uid, body.to_chat_id, new_msg, increment_unread=(uid != user.id))
        forwarded.append(msg_to_response(new_msg))

    await db.commit()

    for resp in forwarded:
        await updates_manager.broadcast_to_chat_members(
            [uid for uid in to_member_ids if uid != user.id],
            {"type": "updateNewMessage", "message": resp.model_dump()},
        )
    return forwarded
