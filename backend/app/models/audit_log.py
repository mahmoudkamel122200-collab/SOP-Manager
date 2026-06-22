"""
AuditLog ORM Model
Table: audit_logs
Module: Cross-cutting (all modules write to this)
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class AuditActionEnum(str, enum.Enum):
    LOGIN            = "LOGIN"
    LOGOUT           = "LOGOUT"
    CREATE           = "CREATE"
    READ             = "READ"
    UPDATE           = "UPDATE"
    DELETE           = "DELETE"
    UPLOAD_DOCUMENT  = "UPLOAD_DOCUMENT"
    OPEN_DOCUMENT    = "OPEN_DOCUMENT"
    UPDATE_DOCUMENT  = "UPDATE_DOCUMENT"
    ARCHIVE_DOCUMENT = "ARCHIVE_DOCUMENT"
    MOVE_ITEM        = "MOVE_ITEM"
    ADD_ITEM         = "ADD_ITEM"
    REMOVE_ITEM      = "REMOVE_ITEM"
    CREATE_LOCATION  = "CREATE_LOCATION"
    CREATE_ITEM      = "CREATE_ITEM"
    SEARCH_ITEM      = "SEARCH_ITEM"
    VIEW_HISTORY     = "VIEW_HISTORY"
    GRANT_ACCESS     = "GRANT_ACCESS"
    REVOKE_ACCESS    = "REVOKE_ACCESS"


class AuditModuleEnum(str, enum.Enum):
    IAM       = "IAM"
    SOP       = "SOP"
    WAREHOUSE = "WAREHOUSE"
    SYSTEM    = "SYSTEM"


class AuditLog(Base):
    """
    Immutable audit trail for all significant user and system actions.
    - user_id is nullable: system events have no actor.
    - target_id is a generic UUID pointing to any affected entity.
    - Rows are NEVER updated or deleted — append only.
    """

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
    user: Mapped[Optional["User"]] = relationship(  # type: ignore[name-defined]
        "User", back_populates="audit_logs"
    )

    __table_args__ = (
        Index("idx_audit_logs_user_id",    "user_id"),
        Index("idx_audit_logs_action",     "action"),
        Index("idx_audit_logs_module",     "module"),
        Index("idx_audit_logs_target_id",  "target_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} module={self.module} user={self.user_id}>"
