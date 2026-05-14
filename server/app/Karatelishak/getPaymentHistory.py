from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.payment import Invoice, Payment
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/payments", tags=["payments"])


class GetPaymentHistoryRequest(BaseModel):
    offset: int = 0
    limit: int = 50


@router.post("/getPaymentHistory")
async def get_payment_history(
    body: GetPaymentHistoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment)
        .where(Payment.payer_id == user.id)
        .order_by(Payment.created_at.desc())
        .offset(body.offset)
        .limit(body.limit)
    )
    payments = result.scalars().all()

    items = []
    for p in payments:
        inv_result = await db.execute(select(Invoice).where(Invoice.id == p.invoice_id))
        inv = inv_result.scalar_one_or_none()
        items.append({
            "id": p.id,
            "amount": p.amount,
            "currency": p.currency,
            "title": inv.title if inv else "",
            "status": p.status,
            "created_at": p.created_at,
        })
    return {"payments": items}
