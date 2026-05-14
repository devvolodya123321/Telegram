from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.Karatelishak.helpers import get_chat_member_ids, update_dialog
from app.database import get_db
from app.models.message import Message
from app.models.payment import Invoice
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/payments", tags=["payments"])


class CreateInvoiceRequest(BaseModel):
    chat_id: int
    title: str
    description: str = ""
    amount: int
    currency: str = "USD"


@router.post("/createInvoice")
async def create_invoice(
    body: CreateInvoiceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_ids = await get_chat_member_ids(db, body.chat_id)
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CHAT_WRITE_FORBIDDEN")

    invoice = Invoice(
        chat_id=body.chat_id,
        creator_id=user.id,
        title=body.title,
        description=body.description,
        amount=body.amount,
        currency=body.currency,
    )
    db.add(invoice)
    await db.flush()

    msg = Message(
        chat_id=body.chat_id,
        from_id=user.id,
        text=f"[Invoice] {body.title} — {body.amount} {body.currency}",
        media_type="invoice",
    )
    db.add(msg)
    await db.flush()

    for uid in member_ids:
        await update_dialog(db, uid, body.chat_id, msg, increment_unread=(uid != user.id))
    await db.commit()
    return {"ok": True, "invoice_id": invoice.id, "message_id": msg.id}
