from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import MessageResponse, get_chat_member_ids, msg_to_response, update_dialog
from app.database import get_db
from app.models.message import Message
from app.models.poll import Poll, PollOption
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/polls", tags=["polls"])


class CreatePollRequest(BaseModel):
    chat_id: int
    question: str
    options: list[str]
    is_anonymous: bool = True
    multiple_choice: bool = False


@router.post("/createPoll")
async def create_poll(
    body: CreatePollRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    poll = Poll(
        chat_id=body.chat_id,
        creator_id=user.id,
        question=body.question,
        is_anonymous=body.is_anonymous,
        multiple_choice=body.multiple_choice,
    )
    db.add(poll)
    await db.flush()

    for i, opt_text in enumerate(body.options):
        db.add(PollOption(poll_id=poll.id, text=opt_text, position=i))

    msg = Message(
        chat_id=body.chat_id,
        from_id=user.id,
        text=f"[Poll] {body.question}",
        media_type="poll",
    )
    db.add(msg)
    await db.flush()

    poll.message_id = msg.id
    for uid in member_ids:
        await update_dialog(db, uid, body.chat_id, msg, increment_unread=(uid != user.id))
    await db.commit()

    return {"ok": True, "poll_id": poll.id, "message_id": msg.id}
