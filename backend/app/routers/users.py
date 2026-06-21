"""
routers/users.py  — Admin-only user management, delegates to UserService.

GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/roles
GET    /api/v1/users/{id}
PATCH  /api/v1/users/{id}
PATCH  /api/v1/users/{id}/block
DELETE /api/v1/users/{id}
GET    /api/v1/users/{id}/sections
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_role
from app.models.role import Role
from app.models.section import UserSection
from app.schemas.user import UserBlockRequest, UserCreateRequest, UserOut, UserUpdateRequest
from app.services.user_service import UserService
from app.utils.responses import paginated_response, success_response

router = APIRouter()
_admin = Depends(require_role("ADMIN"))


def _ip(r: Request) -> str:
    fwd = r.headers.get("X-Forwarded-For")
    return fwd.split(",")[0].strip() if fwd else (r.client.host if r.client else "unknown")


@router.get("", dependencies=[_admin])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    users, total = await UserService(db).list_users(page, page_size)
    return paginated_response(
        data=[UserOut.model_validate(u).model_dump(mode="json") for u in users],
        total=total, page=page, page_size=page_size,
    )


@router.get("/roles", dependencies=[_admin])
async def list_roles(db: AsyncSession = Depends(get_db)):
    """Return all available roles (ADMIN, EMPLOYEE, etc.)."""
    result = await db.execute(select(Role).order_by(Role.name))
    roles = result.scalars().all()
    return success_response(
        data=[
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
            }
            for r in roles
        ]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    request: Request,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).create_user(body, uuid.UUID(token_payload["sub"]), _ip(request))
    return success_response(data=UserOut.model_validate(user).model_dump(mode="json"), status_code=201)


@router.get("/{user_id}", dependencies=[_admin])
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await UserService(db).get_user(user_id)
    return success_response(data=UserOut.model_validate(user).model_dump(mode="json"))


@router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    request: Request,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).update_user(user_id, body, uuid.UUID(token_payload["sub"]), _ip(request))
    return success_response(data=UserOut.model_validate(user).model_dump(mode="json"))


@router.patch("/{user_id}/block")
async def block_user(
    user_id: uuid.UUID,
    body: UserBlockRequest,
    request: Request,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).set_active(user_id, body.is_active, uuid.UUID(token_payload["sub"]), _ip(request))
    return success_response(data={"id": str(user.id), "is_active": user.is_active})


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    await UserService(db).delete_user(user_id, uuid.UUID(token_payload["sub"]), _ip(request))


@router.get("/{user_id}/sections", dependencies=[_admin])
async def get_user_sections(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return all section assignments for a given user."""
    result = await db.execute(
        select(UserSection)
        .where(UserSection.user_id == user_id)
        .options(selectinload(UserSection.section))
    )
    assignments = result.scalars().all()
    return success_response(
        data=[
            {
                "id": str(a.id),
                "user_id": str(a.user_id),
                "section_id": str(a.section_id),
                "section_name": a.section.name if a.section else None,
                "permission_level": a.permission_level.value,
                "created_at": a.created_at.isoformat(),
            }
            for a in assignments
        ]
    )
