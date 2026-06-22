"""
Document ORM Model
Table: documents
Module: SOP Document Management

Soft-delete design:
  is_deleted=True means the document has been logically removed.
  Physical files are NEVER deleted — only the DB record is hidden.
  This preserves auditability and allows recovery.

Versioning design:
  Every upload creates a NEW row. Multiple rows can share the same title
  + section_id, differentiated by their integer version number.
  The service layer auto-increments the version based on the max existing.
"""

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
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class DocumentStatusEnum(str, enum.Enum):
    DRAFT        = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED     = "APPROVED"
    ARCHIVED     = "ARCHIVED"
    REJECTED     = "REJECTED"


class Document(Base):
    """
    SOP document metadata record.

    One row = one version of one document.
    Physical files live on disk (or S3); this row holds the reference path.

    Versioning:
      - `version_number` is an integer (1, 2, 3...) auto-assigned at upload.
      - Documents with the same (title, section_id) form a version family.
      - The service always queries max(version_number) for the "latest".

    Soft delete:
      - `is_deleted=True` hides the document from all lists.
      - Files are never physically removed.
      - `deleted_by` / `deleted_at` preserve the forensic trail.
    """

    __tablename__ = "documents"

    # ── Identity ──────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Section ownership ─────────────────────────────────────────────────────
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Document identity ─────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # ── Version ───────────────────────────────────────────────────────────────
    version_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Auto-assigned integer version (1, 2, 3…)"
    )
    # Human-readable label, e.g. "Rev. A", "2024-Q1" — optional
    version_label: Mapped[Optional[str]] = mapped_column(String(50))

    # ── File ──────────────────────────────────────────────────────────────────
    file_path: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Path relative to UPLOAD_ROOT — never the absolute OS path"
    )
    file_name: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="Original filename as uploaded"
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status: Mapped[DocumentStatusEnum] = mapped_column(
        Enum(DocumentStatusEnum, name="document_status_enum"),
        nullable=False,
        default=DocumentStatusEnum.DRAFT,
    )

    # ── Soft delete ───────────────────────────────────────────────────────────
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column()
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"),
    )

    # ── Uploader ──────────────────────────────────────────────────────────────
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    section: Mapped["Section"] = relationship(  # type: ignore[name-defined]
        "Section", back_populates="documents"
    )
    uploader: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="documents",
        foreign_keys=[uploaded_by],
    )
    deleter: Mapped[Optional["User"]] = relationship(  # type: ignore[name-defined]
        "User",
        foreign_keys=[deleted_by],
    )

    # ── Constraints & indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # Each (title, section, version) must be unique
        UniqueConstraint(
            "title", "section_id", "version_number",
            name="uq_documents_title_section_version",
        ),
        Index("idx_documents_section_id",   "section_id"),
        Index("idx_documents_uploaded_by",  "uploaded_by"),
        Index("idx_documents_status",       "status"),
        Index("idx_documents_is_deleted",   "is_deleted"),
        Index("idx_documents_created_at",   "created_at"),
        # Composite: most common query pattern
        Index(
            "idx_documents_section_deleted_status",
            "section_id", "is_deleted", "status",
        ),
        CheckConstraint("TRIM(title) <> ''",     name="chk_documents_title_not_empty"),
        CheckConstraint("TRIM(file_path) <> ''", name="chk_documents_filepath_not_empty"),
        CheckConstraint("version_number >= 1",   name="chk_documents_version_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<Document title={self.title!r} "
            f"v{self.version_number} status={self.status} "
            f"deleted={self.is_deleted}>"
        )
