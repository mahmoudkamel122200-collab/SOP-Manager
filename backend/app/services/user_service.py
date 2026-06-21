"""
services/user_service.py

User CRUD business logic (Admin operations).
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.user import User
from app.models.role import Role
from app.models.audit_log import AuditActionEnum, AuditModuleEnum
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.audit_service import log_event


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── List (paginated) ──────────────────────────────────────────────────────
    async def list_users(self, page: int, page_size: int) -> tuple[list[User], int]:
        total = (await self.db.execute(select(func.count(User.id)))).scalar_one()
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    # ── Get by ID ─────────────────────────────────────────────────────────────
    async def get_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.role))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    # ── Create ────────────────────────────────────────────────────────────────
    async def create_user(
        self, body: UserCreateRequest, actor_id: uuid.UUID, ip: Optional[str]
    ) -> User:
        # Uniqueness check
        existing = await self.db.execute(
            select(User).where(
                (User.username == body.username) | (User.email == body.email)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists.",
            )

        role = await self.db.get(Role, body.role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

        user = User(
            username=body.username,
            email=body.email,
            password_hash=hash_password(body.password),
            full_name=body.full_name,
            role_id=body.role_id,
        )
        self.db.add(user)
        await self.db.flush()

        await log_event(
            self.db,
            action=AuditActionEnum.CREATE,
            module=AuditModuleEnum.IAM,
            user_id=actor_id,
            target_id=user.id,
            description=f"Created user: {user.username}",
            ip_address=ip,
        )

        await self.db.refresh(user, ["role"])
        return user

    # ── Update ────────────────────────────────────────────────────────────────
    async def update_user(
        self, user_id: uuid.UUID, body: UserUpdateRequest, actor_id: uuid.UUID, ip: Optional[str]
    ) -> User:
        user = await self.get_user(user_id)
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(user, field, value)

        await log_event(
            self.db,
            action=AuditActionEnum.UPDATE,
            module=AuditModuleEnum.IAM,
            user_id=actor_id,
            target_id=user.id,
            description=f"Updated user: {user.username}",
            ip_address=ip,
        )
        await self.db.refresh(user, ["role"])
        return user

    # ── Block / Unblock ───────────────────────────────────────────────────────
    async def set_active(
        self, user_id: uuid.UUID, is_active: bool, actor_id: uuid.UUID, ip: Optional[str]
    ) -> User:
        if user_id == actor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot modify your own active status.",
            )
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        user.is_active = is_active
        label = "activated" if is_active else "blocked"

        await log_event(
            self.db,
            action=AuditActionEnum.UPDATE,
            module=AuditModuleEnum.IAM,
            user_id=actor_id,
            target_id=user.id,
            description=f"User {user.username} {label}.",
            ip_address=ip,
        )
        return user

    # ── Delete ────────────────────────────────────────────────────────────────
    async def delete_user(
        self, user_id: uuid.UUID, actor_id: uuid.UUID, ip: Optional[str]
    ) -> None:
        if user_id == actor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account.",
            )
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        await log_event(
            self.db,
            action=AuditActionEnum.DELETE,
            module=AuditModuleEnum.IAM,
            user_id=actor_id,
            target_id=user.id,
            description=f"Deleted user: {user.username}",
            ip_address=ip,
        )
        await self.db.delete(user)
