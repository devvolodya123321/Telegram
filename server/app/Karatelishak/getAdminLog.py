from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin import AdminLog
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


class GetAdminLogRequest(BaseModel):
    chat_id: int
    offset: int = 0
    limit: int = 50


@router.post("/getAdminLog")
async def get_admin_log(
    body: GetAdminLogRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminLog)
        .where(AdminLog.chat_id == body.chat_id)
        .order_by(AdminLog.created_at.desc())
        .offset(body.offset)
        .limit(body.limit)
    )
    logs = result.scalars().all()
    return {
        "events": [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "action": log.action,
                "target_user_id": log.target_user_id,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ]
    }
