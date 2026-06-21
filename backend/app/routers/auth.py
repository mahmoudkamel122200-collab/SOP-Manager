"""
routers/auth.py

Authentication & Authorization HTTP endpoints.
All business logic lives in AuthService — this file is a pure HTTP adapter.

Endpoints:
  POST /api/v1/auth/login            → credentials → token pair + available sections
  POST /api/v1/auth/select-section   → section_id → section-scoped access token
  POST /api/v1/auth/refresh          → refresh_token → new token pair
  POST /api/v1/auth/logout           → revoke current token (blacklist)
  GET  /api/v1/auth/me               → current user profile + role + sections
  GET  /api/v1/auth/sections         → sections accessible to current user

Complete Auth Flow (Employee):
  1.  POST /login         → get access_token (no section embedded)
                            + available_sections list
  2.  Show section picker in UI from available_sections
  3.  POST /select-section → get new access_token WITH section_id claim
  4.  Use new token for all section-scoped requests
  5.  POST /refresh        → silently rotate tokens (background)
  6.  POST /logout         → revoke token, clear client storage
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_token, get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    RefreshRequest,
    SelectSectionRequest,
)
from app.services.auth_service import AuthService
from app.utils.responses import success_response

router = APIRouter()


def _ip(request: Request) -> str:
    """Extract real client IP, respecting reverse-proxy X-Forwarded-For."""
    fwd = request.headers.get("X-Forwarded-For")
    return fwd.split(",")[0].strip() if fwd else (
        request.client.host if request.client else "unknown"
    )


# =============================================================================
# POST /auth/login
# =============================================================================
@router.post(
    "/login",
    summary="Login with username + password",
    description="""
Returns a JWT token pair plus the list of sections the user can access.

**Employee flow:** Use `available_sections` to render a section picker,
then call `/auth/select-section` to get a section-scoped token.

**Admin flow:** `requires_section_selection` is `false` — the admin token
works globally without section selection.
    """,
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    svc  = AuthService(db)
    data = await svc.login(body.username, body.password, _ip(request))
    return success_response(data=data)


# =============================================================================
# POST /auth/select-section
# =============================================================================
@router.post(
    "/select-section",
    summary="Select active section (Employee: required; Admin: optional)",
    description="""
Embeds a `section_id` claim into a new access token.

**Employee:** Must hold a row in `user_sections` for the requested section.
**Admin:** Can select any section freely.

After a successful call, the client **replaces** its stored `access_token`
with the new section-scoped token returned in the response.
    """,
)
async def select_section(
    body: SelectSectionRequest,
    token_payload: dict = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
):
    svc  = AuthService(db)
    data = await svc.select_section(
        user_id=uuid.UUID(token_payload["sub"]),
        section_id=body.section_id,
        role=token_payload.get("role", ""),
        current_jti=token_payload.get("jti"),
    )
    return success_response(data=data)


# =============================================================================
# POST /auth/refresh
# =============================================================================
@router.post(
    "/refresh",
    summary="Refresh expired access token",
    description="""
Exchange a valid refresh token for a new access + refresh token pair.
Refresh tokens are long-lived (default 7 days).
Call this silently in the background before the access token expires.
    """,
)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc       = AuthService(db)
    token_pair = await svc.refresh(body.refresh_token)
    return success_response(data=token_pair.model_dump())


# =============================================================================
# POST /auth/logout
# =============================================================================
@router.post(
    "/logout",
    summary="Logout — revoke current access token",
    description="""
Adds the current token's JTI to the server-side blacklist.
Any subsequent request using this token will receive **401 Unauthorized**.

The client should also delete its stored tokens (localStorage / cookies).
    """,
)
async def logout(
    request: Request,
    token_payload: dict = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    await svc.logout(
        user_id=uuid.UUID(token_payload["sub"]),
        token_payload=token_payload,
        ip=_ip(request),
    )
    return success_response(
        data={"message": "Logged out successfully. Token has been revoked."}
    )


# =============================================================================
# GET /auth/me
# =============================================================================
@router.get(
    "/me",
    summary="Get current user profile",
    description="""
Returns the full profile of the authenticated user including:
- Identity (id, username, email, full_name)
- Role
- Active section (if selected)
- All accessible sections with permission levels
    """,
)
async def me(
    token_payload: dict = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(token_payload["sub"])

    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.role))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Fetch accessible sections
    svc                = AuthService(db)
    is_admin           = user.role.name == "ADMIN"
    available_sections = await svc.get_my_sections(user_id, is_admin)

    # Active section from token claim
    active_section_id = token_payload.get("section_id")

    return success_response(
        data={
            "id":               str(user.id),
            "username":         user.username,
            "email":            str(user.email),
            "full_name":        user.full_name,
            "role":             user.role.name,
            "is_active":        user.is_active,
            "last_login":       user.last_login.isoformat() if user.last_login else None,
            "active_section_id": active_section_id,
            "available_sections": available_sections,
            "requires_section_selection": not is_admin and not active_section_id,
        }
    )


# =============================================================================
# GET /auth/sections
# =============================================================================
@router.get(
    "/sections",
    summary="Get sections accessible to the current user",
    description="""
Lightweight endpoint to (re)fetch the section list for the section picker UI.
Useful after section assignments have been updated by an admin.
    """,
)
async def my_sections(
    token_payload: dict = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
):
    user_id  = uuid.UUID(token_payload["sub"])
    is_admin = token_payload.get("role") == "ADMIN"

    svc      = AuthService(db)
    sections = await svc.get_my_sections(user_id, is_admin)
    return success_response(data={"sections": sections})
