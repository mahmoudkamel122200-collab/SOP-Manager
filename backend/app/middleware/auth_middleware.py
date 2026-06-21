"""
middleware/auth_middleware.py

Section-level authorization dependency.

The core access control gate for all section-scoped endpoints.

Authorization Model:
  ┌──────────────────────────────────────────────────────────────────┐
  │  ADMIN   → can access everything, no section restriction         │
  │  EMPLOYEE → must select section first, then access is checked    │
  │             against user_sections table                          │
  └──────────────────────────────────────────────────────────────────┘

Permission Hierarchy:
  READ  (0) < WRITE (1) < ADMIN (2)

  READ  → view documents, items, reports
  WRITE → create/move items, upload documents
  ADMIN → manage section assignments, delete records

Decision Flow for every section-protected request:
  1. decode JWT → get user_id, role, section_id
  2. role == ADMIN? → allow immediately (return payload)
  3. section_id missing in JWT? → 403 "select section first"
  4. query user_sections (user_id, section_id) → row found?
  5. no row → 403 "no access to this section"
  6. permission_level >= min_level? → allow (return payload)
  7. no → 403 "insufficient permission"
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_token
from app.models.section import PermissionLevelEnum, UserSection

# ── Permission level ranking ──────────────────────────────────────────────────
_RANK: dict[PermissionLevelEnum, int] = {
    PermissionLevelEnum.READ:  0,
    PermissionLevelEnum.WRITE: 1,
    PermissionLevelEnum.ADMIN: 2,
}


def require_section_permission(
    min_level: PermissionLevelEnum = PermissionLevelEnum.READ,
) -> Callable:
    """
    Dependency factory — returns an async dependency that enforces
    section-level access control.

    Parameters:
        min_level: Minimum permission required. Defaults to READ.

    Returns:
        The token_payload dict so the handler can extract user_id, section_id etc.

    Usage examples:

        # Gate by READ (any section member)
        @router.get("/items", dependencies=[Depends(require_section_permission())])

        # Gate by WRITE (can mutate)
        @router.post("/items")
        async def create(token = Depends(require_section_permission(PermissionLevelEnum.WRITE))):
            user_id = uuid.UUID(token["sub"])

        # Gate by ADMIN (section admin)
        @router.delete("/items/{id}", dependencies=[
            Depends(require_section_permission(PermissionLevelEnum.ADMIN))
        ])
    """

    async def _checker(
        token_payload: dict = Depends(get_current_token),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        role = token_payload.get("role", "")

        # ── STEP 1: ADMIN bypass ─────────────────────────────────────────────
        if role == "ADMIN":
            return token_payload

        # ── STEP 2: section_id must be present in token ──────────────────────
        section_id_raw = token_payload.get("section_id")
        if not section_id_raw:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No active section. "
                    "Call POST /api/v1/auth/select-section to choose a section first."
                ),
            )

        # ── STEP 3: Parse UUIDs ──────────────────────────────────────────────
        try:
            user_id    = uuid.UUID(token_payload["sub"])
            section_id = uuid.UUID(section_id_raw)
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token claims.",
            )

        # ── STEP 4: Query user_sections ──────────────────────────────────────
        result = await db.execute(
            select(UserSection).where(
                UserSection.user_id    == user_id,
                UserSection.section_id == section_id,
            )
        )
        user_section = result.scalar_one_or_none()

        # ── STEP 5: Access granted? ──────────────────────────────────────────
        if not user_section:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this section.",
            )

        # ── STEP 6: Permission level sufficient? ─────────────────────────────
        if _RANK[user_section.permission_level] < _RANK[min_level]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This action requires {min_level.value} permission "
                    f"in this section. Your level: {user_section.permission_level.value}."
                ),
            )

        # ── Allowed ──────────────────────────────────────────────────────────
        return token_payload

    return _checker


# ── Convenience pre-built dependencies ───────────────────────────────────────
# Import these directly instead of calling require_section_permission() inline.

section_read_required  = require_section_permission(PermissionLevelEnum.READ)
section_write_required = require_section_permission(PermissionLevelEnum.WRITE)
section_admin_required = require_section_permission(PermissionLevelEnum.ADMIN)
