"""
Section-aware permission dependency.

Used to check that an authenticated user has access to a specific section
with a required permission level.
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import UserSection, PermissionLevelEnum
from app.security.jwt import get_current_token

# Permission hierarchy — higher index = more powerful
_LEVEL_ORDER = {
    PermissionLevelEnum.READ:  0,
    PermissionLevelEnum.WRITE: 1,
    PermissionLevelEnum.ADMIN: 2,
}


def require_section_permission(min_level: PermissionLevelEnum = PermissionLevelEnum.READ) -> Callable:
    """
    Dependency factory: verifies the current user has at least `min_level`
    permission on the section_id embedded in their JWT.

    Flow:
        1. Decode JWT → extract user_id and section_id
        2. Query user_sections for (user_id, section_id)
        3. Compare permission_level to min_level
        4. Return user_section row or raise 403

    Usage:
        @router.get("/documents/{section_id}")
        async def get_docs(
            section_id: uuid.UUID,
            _: UserSection = Depends(require_section_permission(PermissionLevelEnum.READ)),
        ):
    """

    async def _checker(
        token_payload: dict = Depends(get_current_token),
        db: AsyncSession = Depends(get_db),
    ) -> UserSection:
        # Admins bypass section permission checks
        if token_payload.get("role") == "ADMIN":
            return None  # type: ignore[return-value]

        section_id_raw = token_payload.get("section_id")
        if not section_id_raw:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No section selected. Please select a section first.",
            )

        user_id = uuid.UUID(token_payload["sub"])
        section_id = uuid.UUID(section_id_raw)

        result = await db.execute(
            select(UserSection).where(
                UserSection.user_id == user_id,
                UserSection.section_id == section_id,
            )
        )
        user_section = result.scalar_one_or_none()

        if not user_section:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this section.",
            )

        if _LEVEL_ORDER[user_section.permission_level] < _LEVEL_ORDER[min_level]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires {min_level.value} permission.",
            )

        return user_section

    return _checker
