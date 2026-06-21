"""
services/auth_service.py

Complete authentication business logic.

Flows:
  1. login()          → verify credentials → return tokens + available sections
  2. select_section() → verify access → return section-scoped access token
  3. refresh()        → validate refresh token → return rotated token pair
  4. logout()         → blacklist current access token JTI
  5. get_my_sections()→ return all sections the user can access

Design note:
  The login response deliberately includes `available_sections` so the
  React frontend can immediately render the section picker without a
  second round-trip. This is the recommended pattern for this use case.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.core.config import settings
from app.models.user import User
from app.models.section import Section, UserSection
from app.models.audit_log import AuditActionEnum, AuditModuleEnum
from app.schemas.auth import TokenPair
from app.services.audit_service import log_event
from app.utils.token_blacklist import blacklist


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # LOGIN
    # =========================================================================
    async def login(self, username: str, password: str, ip: str) -> dict:
        """
        Authenticate user credentials and return a full login response.

        Response structure:
          {
            "access_token": str,
            "refresh_token": str,
            "token_type": "bearer",
            "expires_in": int,          ← seconds
            "user": { id, username, email, full_name, role },
            "available_sections": [     ← sections the user can access
              { "id", "name", "description", "permission_level" }
            ],
            "requires_section_selection": bool  ← True for EMPLOYEE
          }

        The frontend uses `available_sections` to render the section picker.
        ADMIN gets requires_section_selection=False and sees all sections.
        """
        # ── 1. Load user with role ──────────────────────────────────────────
        result = await self.db.execute(
            select(User)
            .where(User.username == username)
            .options(selectinload(User.role))
        )
        user: User | None = result.scalar_one_or_none()

        # ── 2. Verify password (constant-time; same error for wrong user/pass)
        if not user or not verify_password(password, user.password_hash):
            await log_event(
                self.db,
                action=AuditActionEnum.LOGIN,
                module=AuditModuleEnum.IAM,
                description=f"Failed login: '{username}'",
                ip_address=ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        # ── 3. Check account is active ──────────────────────────────────────
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled. Contact your administrator.",
            )

        # ── 4. Update last_login ────────────────────────────────────────────
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login=datetime.utcnow())
        )

        # ── 5. Build tokens ─────────────────────────────────────────────────
        is_admin = user.role.name == "ADMIN"

        access_token  = create_access_token(str(user.id), user.role.name)
        refresh_token = create_refresh_token(str(user.id))

        # ── 6. Fetch accessible sections ────────────────────────────────────
        available_sections = await self._get_sections_for_user(user.id, is_admin)

        # ── 7. Write audit log ──────────────────────────────────────────────
        await log_event(
            self.db,
            action=AuditActionEnum.LOGIN,
            module=AuditModuleEnum.IAM,
            user_id=user.id,
            description=f"Login OK — role: {user.role.name}",
            ip_address=ip,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id":        str(user.id),
                "username":  user.username,
                "email":     str(user.email),
                "full_name": user.full_name,
                "role":      user.role.name,
            },
            "available_sections": available_sections,
            "requires_section_selection": not is_admin,
        }

    # =========================================================================
    # SECTION SELECTION
    # =========================================================================
    async def select_section(
        self,
        user_id: uuid.UUID,
        section_id: uuid.UUID,
        role: str,
        current_jti: str | None = None,
    ) -> dict:
        """
        Validate section access and return a section-scoped access token.

        Rules:
          - ADMIN can select ANY section (used for browsing a specific dept).
          - EMPLOYEE must have a row in user_sections for the requested section.
          - A new access_token is issued with section_id embedded as a claim.
          - The old access_token is NOT blacklisted (it remains valid for the
            remaining TTL — acceptable for MVP; use Redis TTL matching in prod).

        After calling this endpoint, the client replaces its stored access_token
        with the new section-scoped one. All subsequent API calls use the new token.
        """
        is_admin = (role == "ADMIN")

        # ── Verify section exists ───────────────────────────────────────────
        section = await self.db.get(Section, section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found.",
            )

        # ── Permission check ────────────────────────────────────────────────
        if is_admin:
            # Admins can enter any section — synthesise a virtual ADMIN perm
            permission_level = "ADMIN"
        else:
            result = await self.db.execute(
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
            permission_level = user_section.permission_level.value

        # ── Mint section-scoped token ────────────────────────────────────────
        new_access_token = create_access_token(
            user_id=str(user_id),
            role=role,
            section_id=str(section_id),
        )

        return {
            "access_token": new_access_token,
            "token_type":   "bearer",
            "section": {
                "id":          str(section.id),
                "name":        section.name,
                "description": section.description,
            },
            "permission_level": permission_level,
            "message": f"Active section set to '{section.name}'.",
        }

    # =========================================================================
    # REFRESH TOKEN
    # =========================================================================
    async def refresh(self, refresh_token_str: str) -> TokenPair:
        """
        Exchange a valid refresh token for a new access + refresh token pair.

        Refresh token rotation:
          - Old refresh token remains valid until natural expiry (MVP).
          - Production: blacklist old refresh JTI immediately after rotation.
        """
        payload = decode_refresh_token(refresh_token_str)
        user_id = uuid.UUID(payload["sub"])

        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role))
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        return TokenPair(
            access_token=create_access_token(str(user.id), user.role.name),
            refresh_token=create_refresh_token(str(user.id)),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # =========================================================================
    # LOGOUT
    # =========================================================================
    async def logout(
        self,
        user_id: uuid.UUID,
        token_payload: dict,
        ip: str,
    ) -> None:
        """
        Invalidate the current access token by adding its JTI to the blacklist.

        The token will be rejected by decode_access_token() for all subsequent
        requests, even though it hasn't naturally expired yet.
        """
        from datetime import datetime, timezone
        import datetime as dt

        jti = token_payload.get("jti")
        exp = token_payload.get("exp")

        if jti and exp:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            blacklist.add(jti, expires_at)

        await log_event(
            self.db,
            action=AuditActionEnum.LOGOUT,
            module=AuditModuleEnum.IAM,
            user_id=user_id,
            description="User logged out — token revoked.",
            ip_address=ip,
        )

    # =========================================================================
    # GET MY SECTIONS  (/auth/me and /auth/sections)
    # =========================================================================
    async def get_my_sections(self, user_id: uuid.UUID, is_admin: bool) -> list[dict]:
        """Return sections accessible to the user with their permission levels."""
        return await self._get_sections_for_user(user_id, is_admin)

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    async def _get_sections_for_user(
        self, user_id: uuid.UUID, is_admin: bool
    ) -> list[dict]:
        """
        Internal: Build the sections list for the login response and /me.

        ADMIN → all sections (with virtual ADMIN permission)
        EMPLOYEE → only sections in user_sections
        """
        if is_admin:
            result = await self.db.execute(
                select(Section).order_by(Section.name)
            )
            return [
                {
                    "id":               str(s.id),
                    "name":             s.name,
                    "description":      s.description,
                    "permission_level": "ADMIN",
                }
                for s in result.scalars().all()
            ]

        # EMPLOYEE: join user_sections to get per-section permission
        result = await self.db.execute(
            select(Section, UserSection.permission_level)
            .join(UserSection, UserSection.section_id == Section.id)
            .where(UserSection.user_id == user_id)
            .order_by(Section.name)
        )
        return [
            {
                "id":               str(section.id),
                "name":             section.name,
                "description":      section.description,
                "permission_level": perm.value,
            }
            for section, perm in result.all()
        ]
