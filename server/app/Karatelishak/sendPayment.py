from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.payment import Invoice, Payment
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/payments", tags=["payments"])


class SendPaymentRequest(BaseModel):
    invoice_id: int


@router.post("/sendPayment")
async def send_payment(
    body: SendPaymentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Invoice).where(Invoice.id == body.invoice_id))
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="INVOICE_NOT_FOUND")
    if invoice.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVOICE_ALREADY_PAID")

    payment = Payment(
        invoice_id=invoice.id,
        payer_id=user.id,
        amount=invoice.amount,
        currency=invoice.currency,
    )
    db.add(payment)
    invoice.status = "paid"
    await db.commit()
    return {"ok": True, "payment_id": payment.id}
