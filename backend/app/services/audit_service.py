"""
Audit logging service — thin async helper used across all routers.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuditLog, AuditActionEnum, AuditModuleEnum


async def log_event(
    db: AsyncSession,
    *,
    action: AuditActionEnum,
    module: AuditModuleEnum,
    user_id: Optional[uuid.UUID] = None,
    target_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Append an immutable audit log entry.

    Called directly from routers/services — never from models.
    The session is committed by the get_db dependency after the request.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        module=module,
        target_id=target_id,
        description=description,
        ip_address=ip_address,
    )
    db.add(entry)
    # NOTE: do NOT await db.commit() here — let the dependency handle it
    #       so all writes in the request are atomic.
