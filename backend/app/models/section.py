"""
Section & UserSection ORM Models
Tables: sections, user_sections
Module: Identity & Access Management
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class PermissionLevelEnum(str, enum.Enum):
    READ  = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class Section(Base):
    """Represents a factory department (Production, Labs, Warehouse, Quality…)."""

    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    user_permissions: Mapped[list["UserSection"]] = relationship(
        "UserSection", back_populates="section", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(  # type: ignore[name-defined]
        "Document", back_populates="section"
    )

    __table_args__ = (
        CheckConstraint("TRIM(name) <> ''", name="chk_sections_name_not_empty"),
    )

    def __repr__(self) -> str:
        return f"<Section name={self.name!r}>"


class UserSection(Base):
    """
    Junction table: Users ↔ Sections (M:N) with a per-section permission level.
    Controls which employees can access which factory departments.
    """

    __tablename__ = "user_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    permission_level: Mapped[PermissionLevelEnum] = mapped_column(
        Enum(PermissionLevelEnum, name="permission_level_enum"),
        nullable=False,
        default=PermissionLevelEnum.READ,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="section_permissions")  # type: ignore[name-defined]
    section: Mapped["Section"] = relationship("Section", back_populates="user_permissions")

    __table_args__ = (
        UniqueConstraint("user_id", "section_id", name="uq_user_sections_user_section"),
        Index("idx_user_sections_user_id",    "user_id"),
        Index("idx_user_sections_section_id", "section_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserSection user={self.user_id} "
            f"section={self.section_id} level={self.permission_level}>"
        )
