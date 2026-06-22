"""
Sections Router

GET    /api/v1/sections              — list (authenticated)
POST   /api/v1/sections              — create (Admin)
DELETE /api/v1/sections/{id}         — delete (Admin)
GET    /api/v1/sections/my           — sections accessible to current user
POST   /api/v1/sections/assign       — assign user to section (Admin)
DELETE /api/v1/sections/assign/{id}  — revoke access (Admin)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import (
    AuditActionEnum,
    AuditModuleEnum,
    Section,
    UserSection,
    PermissionLevelEnum,
)
from app.schemas.schemas import (
    SectionCreateRequest,
    SectionOut,
    UserSectionAssignRequest,
    UserSectionOut,
)
from app.security.jwt import get_current_token, require_role
from app.services.audit_service import log_event
from app.utils.responses import success_response

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /sections  — all sections (any authenticated user)
# ---------------------------------------------------------------------------
@router.get("")
async def list_sections(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Section).order_by(Section.name))
    sections = result.scalars().all()
    return success_response(
        data=[SectionOut.model_validate(s).model_dump(mode="json") for s in sections]
    )


# ---------------------------------------------------------------------------
# GET /sections/my  — sections the current user can access
# ---------------------------------------------------------------------------
@router.get("/my")
async def my_sections(
    token_payload: dict = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(token_payload["sub"])
    result = await db.execute(
        select(Section)
        .join(UserSection, UserSection.section_id == Section.id)
        .where(UserSection.user_id == user_id)
        .order_by(Section.name)
    )
    sections = result.scalars().all()
    return success_response(
        data=[SectionOut.model_validate(s).model_dump(mode="json") for s in sections]
    )


# ---------------------------------------------------------------------------
# POST /sections  — create section (Admin)
# ---------------------------------------------------------------------------
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_section(
    body: SectionCreateRequest,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Section).where(Section.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Section name already exists.")

    section = Section(name=body.name, description=body.description)
    db.add(section)
    await db.flush()

    await log_event(
        db,
        action=AuditActionEnum.CREATE,
        module=AuditModuleEnum.IAM,
        user_id=uuid.UUID(token_payload["sub"]),
        target_id=section.id,
        description=f"Created section: {section.name}",
    )

    return success_response(
        data=SectionOut.model_validate(section).model_dump(mode="json"),
        status_code=201,
    )


# ---------------------------------------------------------------------------
# DELETE /sections/{id}  — delete (Admin)
# ---------------------------------------------------------------------------
@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: uuid.UUID,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    section = await db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")

    await log_event(
        db,
        action=AuditActionEnum.DELETE,
        module=AuditModuleEnum.IAM,
        user_id=uuid.UUID(token_payload["sub"]),
        target_id=section.id,
        description=f"Deleted section: {section.name}",
    )
    await db.delete(section)


# ---------------------------------------------------------------------------
# POST /sections/assign  — assign user to section (Admin)
# ---------------------------------------------------------------------------
@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_user_to_section(
    body: UserSectionAssignRequest,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(UserSection).where(
            UserSection.user_id == body.user_id,
            UserSection.section_id == body.section_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already assigned to this section.")

    us = UserSection(
        user_id=body.user_id,
        section_id=body.section_id,
        permission_level=body.permission_level,
    )
    db.add(us)
    await db.flush()

    await log_event(
        db,
        action=AuditActionEnum.GRANT_ACCESS,
        module=AuditModuleEnum.IAM,
        user_id=uuid.UUID(token_payload["sub"]),
        target_id=us.id,
        description=f"Granted {body.permission_level.value} access to section {body.section_id} for user {body.user_id}",
    )

    return success_response(
        data=UserSectionOut.model_validate(us).model_dump(mode="json"),
        status_code=201,
    )


# ---------------------------------------------------------------------------
# DELETE /sections/assign/{user_section_id}  — revoke access (Admin)
# ---------------------------------------------------------------------------
@router.delete("/assign/{user_section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_section_access(
    user_section_id: uuid.UUID,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    us = await db.get(UserSection, user_section_id)
    if not us:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

    await log_event(
        db,
        action=AuditActionEnum.REVOKE_ACCESS,
        module=AuditModuleEnum.IAM,
        user_id=uuid.UUID(token_payload["sub"]),
        target_id=us.id,
        description=f"Revoked access for user {us.user_id} from section {us.section_id}",
    )
    await db.delete(us)
