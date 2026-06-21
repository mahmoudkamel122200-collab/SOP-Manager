"""
Factory Management System — SQLAlchemy ORM Models
Database: PostgreSQL 15+
ORM: SQLAlchemy 2.x (mapped_column / DeclarativeBase)

Install dependencies:
    pip install sqlalchemy[asyncio] asyncpg greenlet
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import CITEXT, INET, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Python-side Enums (mirror the PostgreSQL enums)
# ---------------------------------------------------------------------------
class PermissionLevelEnum(str, enum.Enum):
    READ  = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class DocumentStatusEnum(str, enum.Enum):
    DRAFT        = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED     = "APPROVED"
    ARCHIVED     = "ARCHIVED"
    REJECTED     = "REJECTED"


class ItemStatusEnum(str, enum.Enum):
    AVAILABLE  = "AVAILABLE"
    RESERVED   = "RESERVED"
    CONSUMED   = "CONSUMED"
    DAMAGED    = "DAMAGED"
    QUARANTINE = "QUARANTINE"


class AuditActionEnum(str, enum.Enum):
    LOGIN            = "LOGIN"
    LOGOUT           = "LOGOUT"
    CREATE           = "CREATE"
    READ             = "READ"
    UPDATE           = "UPDATE"
    DELETE           = "DELETE"
    UPLOAD_DOCUMENT  = "UPLOAD_DOCUMENT"
    OPEN_DOCUMENT    = "OPEN_DOCUMENT"
    ARCHIVE_DOCUMENT = "ARCHIVE_DOCUMENT"
    MOVE_ITEM        = "MOVE_ITEM"
    ADD_ITEM         = "ADD_ITEM"
    REMOVE_ITEM      = "REMOVE_ITEM"
    GRANT_ACCESS     = "GRANT_ACCESS"
    REVOKE_ACCESS    = "REVOKE_ACCESS"


class AuditModuleEnum(str, enum.Enum):
    IAM       = "IAM"
    SOP       = "SOP"
    WAREHOUSE = "WAREHOUSE"
    SYSTEM    = "SYSTEM"


# =============================================================================
# MODULE 1 — IDENTITY & ACCESS MANAGEMENT
# =============================================================================

class Role(Base):
    """User roles for RBAC."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

    __table_args__ = (
        CheckConstraint("TRIM(name) <> ''", name="chk_roles_name_not_empty"),
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"


class User(Base):
    """System user with hashed credentials and role assignment."""

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
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    section_permissions: Mapped[list["UserSection"]] = relationship(
        "UserSection", back_populates="user"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="uploader"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )
    items_created: Mapped[list["Item"]] = relationship(
        "Item", back_populates="creator"
    )
    movements: Mapped[list["MovementLog"]] = relationship(
        "MovementLog", back_populates="mover"
    )

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_role_id", "role_id"),
        CheckConstraint("LENGTH(TRIM(username)) >= 3", name="chk_users_username_len"),
        CheckConstraint("LENGTH(password_hash) >= 60",  name="chk_users_password_len"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


class Section(Base):
    """Factory department / section."""

    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    user_permissions: Mapped[list["UserSection"]] = relationship(
        "UserSection", back_populates="section"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="section"
    )

    __table_args__ = (
        CheckConstraint("TRIM(name) <> ''", name="chk_sections_name_not_empty"),
    )

    def __repr__(self) -> str:
        return f"<Section id={self.id} name={self.name!r}>"


class UserSection(Base):
    """Junction table — Users ↔ Sections with a permission level."""

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
    user: Mapped["User"] = relationship("User", back_populates="section_permissions")
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


# =============================================================================
# MODULE 2 — SOP DOCUMENT MANAGEMENT
# =============================================================================

class Document(Base):
    """SOP document metadata record."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[DocumentStatusEnum] = mapped_column(
        Enum(DocumentStatusEnum, name="document_status_enum"),
        nullable=False,
        default=DocumentStatusEnum.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    section: Mapped["Section"] = relationship("Section", back_populates="documents")
    uploader: Mapped["User"] = relationship("User", back_populates="documents")

    __table_args__ = (
        Index("idx_documents_section_id",  "section_id"),
        Index("idx_documents_uploaded_by", "uploaded_by"),
        Index("idx_documents_status",      "status"),
        CheckConstraint("TRIM(title) <> ''",     name="chk_documents_title_not_empty"),
        CheckConstraint("TRIM(file_path) <> ''", name="chk_documents_filepath_not_empty"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title!r} v{self.version}>"


class AuditLog(Base):
    """Immutable audit trail for all user and system actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    action: Mapped[AuditActionEnum] = mapped_column(
        Enum(AuditActionEnum, name="audit_action_enum"), nullable=False
    )
    module: Mapped[AuditModuleEnum] = mapped_column(
        Enum(AuditModuleEnum, name="audit_module_enum"), nullable=False
    )
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    description: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_user_id",    "user_id"),
        Index("idx_audit_logs_action",     "action"),
        Index("idx_audit_logs_module",     "module"),
        Index("idx_audit_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} module={self.module}>"


# =============================================================================
# MODULE 3 — WAREHOUSE MANAGEMENT
# =============================================================================

class Location(Base):
    """Physical warehouse storage position."""

    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    warehouse_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rack: Mapped[str] = mapped_column(String(20), nullable=False)
    shelf: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[str] = mapped_column(String(20), nullable=False)
    location_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    items: Mapped[list["Item"]] = relationship("Item", back_populates="location")
    movements_from: Mapped[list["MovementLog"]] = relationship(
        "MovementLog",
        foreign_keys="MovementLog.from_location",
        back_populates="from_loc",
    )
    movements_to: Mapped[list["MovementLog"]] = relationship(
        "MovementLog",
        foreign_keys="MovementLog.to_location",
        back_populates="to_loc",
    )

    __table_args__ = (
        Index("idx_locations_warehouse_name", "warehouse_name"),
        Index("idx_locations_location_code",  "location_code"),
    )

    def __repr__(self) -> str:
        return f"<Location code={self.location_code!r}>"


class Item(Base):
    """Warehoused material or bag."""

    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    material_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ItemStatusEnum] = mapped_column(
        Enum(ItemStatusEnum, name="item_status_enum"),
        nullable=False,
        default=ItemStatusEnum.AVAILABLE,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    location: Mapped["Location"] = relationship("Location", back_populates="items")
    creator: Mapped["User"] = relationship("User", back_populates="items_created")
    movement_logs: Mapped[list["MovementLog"]] = relationship(
        "MovementLog", back_populates="item"
    )

    __table_args__ = (
        Index("idx_items_item_code",   "item_code"),
        Index("idx_items_location_id", "location_id"),
        Index("idx_items_status",      "status"),
        CheckConstraint("quantity >= 0", name="chk_items_quantity_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Item code={self.item_code!r} qty={self.quantity} {self.unit}>"


class MovementLog(Base):
    """Immutable ledger of warehouse item movements."""

    __tablename__ = "movement_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    from_location: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    to_location: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    moved_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    item: Mapped["Item"] = relationship("Item", back_populates="movement_logs")
    from_loc: Mapped[Optional["Location"]] = relationship(
        "Location",
        foreign_keys=[from_location],
        back_populates="movements_from",
    )
    to_loc: Mapped["Location"] = relationship(
        "Location",
        foreign_keys=[to_location],
        back_populates="movements_to",
    )
    mover: Mapped["User"] = relationship("User", back_populates="movements")

    __table_args__ = (
        Index("idx_movement_logs_item_id",    "item_id"),
        Index("idx_movement_logs_to_location", "to_location"),
        Index("idx_movement_logs_moved_by",    "moved_by"),
        Index("idx_movement_logs_created_at",  "created_at"),
        CheckConstraint(
            "from_location IS NULL OR from_location <> to_location",
            name="chk_movement_logs_different_locations",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MovementLog item={self.item_id} "
            f"from={self.from_location} to={self.to_location}>"
        )
