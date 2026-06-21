"""
User ORM Model
Table: users
Module: Identity & Access Management
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(150))
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column()

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users")  # type: ignore[name-defined]
    section_permissions: Mapped[list["UserSection"]] = relationship(  # type: ignore[name-defined]
        "UserSection", back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(  # type: ignore[name-defined]
        "Document", back_populates="uploader", foreign_keys="Document.uploaded_by"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]
        "AuditLog", back_populates="user"
    )
    items_created: Mapped[list["Item"]] = relationship(  # type: ignore[name-defined]
        "Item", back_populates="creator"
    )
    movements: Mapped[list["MovementLog"]] = relationship(  # type: ignore[name-defined]
        "MovementLog", back_populates="mover", foreign_keys="MovementLog.moved_by"
    )

    __table_args__ = (
        Index("idx_users_username",  "username"),
        Index("idx_users_email",     "email"),
        Index("idx_users_role_id",   "role_id"),
        CheckConstraint("LENGTH(TRIM(username)) >= 3", name="chk_users_username_len"),
        CheckConstraint("LENGTH(password_hash) >= 60", name="chk_users_password_len"),
    )

    def __repr__(self) -> str:
        return f"<User username={self.username!r} role_id={self.role_id}>"
