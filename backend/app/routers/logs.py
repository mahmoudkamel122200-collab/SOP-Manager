"""
routers/logs.py
Global audit logs endpoint.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_role
from app.models.models import AuditLog

router = APIRouter()

@router.get(
    "",
    summary="[Admin] Get global audit logs",
)
async def get_all_logs(
    limit: int = Query(100, ge=1, le=1000),
    _payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    data = []
    for log in logs:
        data.append({
            "id": str(log.id),
            "username": log.user.username if log.user else "System",
            "action": log.action.value if hasattr(log.action, 'value') else log.action,
            "module": log.module.value if hasattr(log.module, 'value') else log.module,
            "resource_type": log.module.value if hasattr(log.module, 'value') else log.module,
            "description": log.description,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
            "timestamp": log.created_at.isoformat(),
        })

    return {"status": "success", "data": data}
