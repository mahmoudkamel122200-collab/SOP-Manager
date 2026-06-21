"""
services/document_service.py

SOP Document Management — complete business logic layer.

Responsibilities:
  ┌──────────────────────────────────────────────────────────────────┐
  │  UPLOAD      validate → auto-version → save file → DB record     │
  │  LIST        section-scoped list with search + status filter     │
  │  LIST ALL    admin-only: across all sections                     │
  │  GET         permission-checked metadata fetch + OPEN audit log  │
  │  DOWNLOAD    resolve file path for streaming                     │
  │  VERSIONS    list all versions of a document by title+section    │
  │  STATUS      lifecycle transitions (DRAFT → APPROVED → ARCHIVED) │
  │  DELETE      soft delete — sets is_deleted=True, never removes   │
  │  LOGS        full audit trail for a specific document            │
  └──────────────────────────────────────────────────────────────────┘

Access control:
  ADMIN  → can access all documents in all sections
  EMPLOYEE → can only access documents in sections from user_sections;
             the token's active section_id is checked for list endpoints
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, DocumentStatusEnum
from app.models.audit_log import AuditLog, AuditActionEnum, AuditModuleEnum
from app.models.section import Section, UserSection
from app.services.audit_service import log_event
from app.services.storage_service import (
    StorageBackend,
    validate_upload_file,
    read_and_validate_content,
)

# ── Valid status transition graph ─────────────────────────────────────────────
# Key = current status, Value = set of allowed next statuses
STATUS_TRANSITIONS: dict[DocumentStatusEnum, set[DocumentStatusEnum]] = {
    DocumentStatusEnum.DRAFT:        {DocumentStatusEnum.UNDER_REVIEW, DocumentStatusEnum.ARCHIVED},
    DocumentStatusEnum.UNDER_REVIEW: {DocumentStatusEnum.APPROVED, DocumentStatusEnum.REJECTED, DocumentStatusEnum.DRAFT},
    DocumentStatusEnum.APPROVED:     {DocumentStatusEnum.ARCHIVED},
    DocumentStatusEnum.REJECTED:     {DocumentStatusEnum.DRAFT},
    DocumentStatusEnum.ARCHIVED:     set(),   # terminal — no further transitions
}


class DocumentService:

    def __init__(self, db: AsyncSession, storage: StorageBackend):
        self.db      = db
        self.storage = storage

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    async def _get_section_or_404(self, section_id: uuid.UUID) -> Section:
        section = await self.db.get(Section, section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section '{section_id}' not found.",
            )
        return section

    async def _get_document_or_404(self, doc_id: uuid.UUID) -> Document:
        result = await self.db.execute(
            select(Document)
            .where(Document.id == doc_id, Document.is_deleted == False)  # noqa: E712
            .options(
                selectinload(Document.section),
                selectinload(Document.uploader),
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        return doc

    async def _verify_section_access(
        self,
        user_id: uuid.UUID,
        section_id: uuid.UUID,
        role: str,
    ) -> None:
        """Raise 403 if an EMPLOYEE doesn't have access to section_id."""
        if role == "ADMIN":
            return
        result = await self.db.execute(
            select(UserSection).where(
                UserSection.user_id    == user_id,
                UserSection.section_id == section_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this section.",
            )

    async def _next_version_number(self, title: str, section_id: uuid.UUID) -> int:
        """
        Return the next auto-incremented version number for a document.

        Logic:
          1. Find max(version_number) for docs with the same title in the same section.
          2. Return max + 1, or 1 if no previous versions exist.
        """
        result = await self.db.execute(
            select(func.max(Document.version_number)).where(
                Document.title      == title,
                Document.section_id == section_id,
                Document.is_deleted == False,  # noqa: E712
            )
        )
        max_version: Optional[int] = result.scalar_one_or_none()
        return (max_version or 0) + 1

    # =========================================================================
    # LIST — documents in a section
    # =========================================================================

    async def list_by_section(
        self,
        section_id:      uuid.UUID,
        user_id:         uuid.UUID,
        role:            str,
        search:          Optional[str]               = None,
        status_filter:   Optional[DocumentStatusEnum] = None,
        include_archived: bool                       = False,
        page:            int                         = 1,
        page_size:       int                         = 20,
    ) -> tuple[list[Document], int]:
        """
        Return paginated documents for a section.

        Access:
          ADMIN  → any section
          EMPLOYEE → only their assigned sections; active section_id in JWT must match
        """
        await self._verify_section_access(user_id, section_id, role)

        q = (
            select(Document)
            .where(
                Document.section_id == section_id,
                Document.is_deleted == False,  # noqa: E712
            )
            .options(selectinload(Document.section), selectinload(Document.uploader))
        )

        # Status filter
        if status_filter:
            q = q.where(Document.status == status_filter)
        elif not include_archived:
            q = q.where(Document.status != DocumentStatusEnum.ARCHIVED)

        # Full-text search on title + description
        if search:
            term = f"%{search.lower()}%"
            q = q.where(
                or_(
                    func.lower(Document.title).like(term),
                    func.lower(Document.description).like(term),
                )
            )

        # Total count
        count_q  = select(func.count()).select_from(q.subquery())
        total    = (await self.db.execute(count_q)).scalar_one()

        # Paginate — order by version desc, then creation time desc
        q = (
            q.order_by(Document.title, Document.version_number.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
        )
        docs = (await self.db.execute(q)).scalars().all()
        return docs, total

    # =========================================================================
    # LIST ALL — admin-only across all sections
    # =========================================================================

    async def list_all(
        self,
        search:        Optional[str]               = None,
        status_filter: Optional[DocumentStatusEnum] = None,
        section_id:    Optional[uuid.UUID]         = None,
        page:          int                         = 1,
        page_size:     int                         = 20,
    ) -> tuple[list[Document], int]:
        """Admin-only: list every document across all sections."""
        q = (
            select(Document)
            .where(Document.is_deleted == False)  # noqa: E712
            .options(selectinload(Document.section), selectinload(Document.uploader))
        )

        if section_id:
            q = q.where(Document.section_id == section_id)
        if status_filter:
            q = q.where(Document.status == status_filter)
        if search:
            term = f"%{search.lower()}%"
            q = q.where(
                or_(
                    func.lower(Document.title).like(term),
                    func.lower(Document.description).like(term),
                )
            )

        total = (await self.db.execute(
            select(func.count()).select_from(q.subquery())
        )).scalar_one()

        docs = (await self.db.execute(
            q.order_by(Document.section_id, Document.title, Document.version_number.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
        )).scalars().all()

        return docs, total

    # =========================================================================
    # UPLOAD — with auto-versioning
    # =========================================================================

    async def upload(
        self,
        *,
        section_id:    uuid.UUID,
        title:         str,
        description:   Optional[str],
        version_label: Optional[str],
        file:          UploadFile,
        uploader_id:   uuid.UUID,
        ip:            Optional[str],
    ) -> Document:
        """
        Upload a new SOP document.

        Auto-versioning:
          If documents with the same title already exist in this section,
          the new upload is automatically assigned version_number = max + 1.
          This means you NEVER need to pass a version manually.

        File naming (disk):
          {section_slug}/{title_slug}_v{version}_{epoch}.{ext}

        Example:
          production/machine_safety_sop_v1_1750424400.pdf
          production/machine_safety_sop_v2_1750511000.pdf  ← new upload
        """
        # ── 1. Validate section ────────────────────────────────────────────
        section = await self._get_section_or_404(section_id)

        # ── 2. Validate file ───────────────────────────────────────────────
        ext, mime = validate_upload_file(file)
        content   = await read_and_validate_content(file)

        # ── 3. Auto-assign version ─────────────────────────────────────────
        version_number = await self._next_version_number(title, section_id)

        # ── 4. Persist file to storage backend ────────────────────────────
        relative_path, stored_filename = await self.storage.save(
            content=content,
            title=title,
            version_number=version_number,
            section_name=section.name,
            extension=ext,
        )

        # ── 5. Create DB record ────────────────────────────────────────────
        doc = Document(
            section_id=section_id,
            title=title,
            description=description,
            version_number=version_number,
            version_label=version_label,
            file_path=relative_path,
            file_name=file.filename or stored_filename,
            file_size_bytes=len(content),
            mime_type=mime,
            uploaded_by=uploader_id,
            status=DocumentStatusEnum.DRAFT,
        )
        self.db.add(doc)
        await self.db.flush()    # materialise doc.id

        # ── 6. Audit ───────────────────────────────────────────────────────
        await log_event(
            self.db,
            action=AuditActionEnum.UPLOAD_DOCUMENT,
            module=AuditModuleEnum.SOP,
            user_id=uploader_id,
            target_id=doc.id,
            description=(
                f"Uploaded '{title}' v{version_number} "
                f"({len(content) // 1024} KB) → section '{section.name}'"
            ),
            ip_address=ip,
        )

        await self.db.refresh(doc, ["section", "uploader"])
        return doc

    # =========================================================================
    # GET — fetch metadata + permission check
    # =========================================================================

    async def get(
        self,
        doc_id:  uuid.UUID,
        user_id: uuid.UUID,
        role:    str,
        ip:      Optional[str] = None,
    ) -> Document:
        """
        Fetch a document's metadata.
        Employees can only view documents in their assigned sections.
        Every successful open is logged as OPEN_DOCUMENT.
        """
        doc = await self._get_document_or_404(doc_id)

        # ── Permission check ───────────────────────────────────────────────
        await self._verify_section_access(user_id, doc.section_id, role)

        # ── Audit ──────────────────────────────────────────────────────────
        await log_event(
            self.db,
            action=AuditActionEnum.OPEN_DOCUMENT,
            module=AuditModuleEnum.SOP,
            user_id=user_id,
            target_id=doc.id,
            description=f"Opened: '{doc.title}' v{doc.version_number}",
            ip_address=ip,
        )
        return doc

    # =========================================================================
    # DOWNLOAD — resolve physical file path for streaming
    # =========================================================================

    async def resolve_for_download(
        self,
        doc_id:  uuid.UUID,
        user_id: uuid.UUID,
        role:    str,
        ip:      Optional[str] = None,
    ) -> tuple[Path, str, str]:
        """
        Return (absolute_path, filename, mime_type) for the document.
        Permission is checked the same way as `get()`.
        No additional OPEN_DOCUMENT log is written (the download IS the open).
        """
        doc = await self._get_document_or_404(doc_id)
        await self._verify_section_access(user_id, doc.section_id, role)

        abs_path = self.storage.resolve(doc.file_path)
        if not abs_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on storage. Contact your administrator.",
            )

        await log_event(
            self.db,
            action=AuditActionEnum.OPEN_DOCUMENT,
            module=AuditModuleEnum.SOP,
            user_id=user_id,
            target_id=doc.id,
            description=f"Downloaded: '{doc.title}' v{doc.version_number}",
            ip_address=ip,
        )

        mime = doc.mime_type or "application/octet-stream"
        return abs_path, doc.file_name, mime

    # =========================================================================
    # VERSION HISTORY — all versions of a title in a section
    # =========================================================================

    async def get_versions(
        self,
        doc_id:  uuid.UUID,
        user_id: uuid.UUID,
        role:    str,
    ) -> list[Document]:
        """
        Return all versions (newest first) of the document identified by doc_id.
        Uses the doc's title + section_id to find the version family.
        """
        doc = await self._get_document_or_404(doc_id)
        await self._verify_section_access(user_id, doc.section_id, role)

        result = await self.db.execute(
            select(Document)
            .where(
                Document.title      == doc.title,
                Document.section_id == doc.section_id,
                Document.is_deleted == False,  # noqa: E712
            )
            .options(selectinload(Document.uploader))
            .order_by(Document.version_number.desc())
        )
        return result.scalars().all()

    # =========================================================================
    # STATUS TRANSITION
    # =========================================================================

    async def update_status(
        self,
        doc_id:     uuid.UUID,
        new_status: DocumentStatusEnum,
        actor_id:   uuid.UUID,
        ip:         Optional[str] = None,
    ) -> Document:
        """
        Transition a document through its lifecycle.

        Valid transitions:
          DRAFT → UNDER_REVIEW → APPROVED → ARCHIVED
          UNDER_REVIEW → REJECTED → DRAFT
        """
        doc = await self._get_document_or_404(doc_id)
        old_status = doc.status

        allowed = STATUS_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot transition '{old_status.value}' → '{new_status.value}'. "
                    f"Allowed transitions: {[s.value for s in allowed] or 'none (terminal state)'}."
                ),
            )

        doc.status = new_status

        await log_event(
            self.db,
            action=AuditActionEnum.UPDATE,
            module=AuditModuleEnum.SOP,
            user_id=actor_id,
            target_id=doc.id,
            description=f"'{doc.title}' v{doc.version_number}: {old_status.value} → {new_status.value}",
            ip_address=ip,
        )
        return doc

    # =========================================================================
    # SOFT DELETE
    # =========================================================================

    async def soft_delete(
        self,
        doc_id:   uuid.UUID,
        actor_id: uuid.UUID,
        ip:       Optional[str] = None,
    ) -> None:
        """
        Soft-delete a document.

        What happens:
          1. Sets is_deleted=True on the DB record.
          2. Records deleted_at, deleted_by.
          3. Writes a DELETE_DOCUMENT audit log.
          4. The physical file is intentionally NOT removed.

        The document is invisible to all list/get queries.
        An admin can still see it by querying include_deleted=true.
        """
        doc = await self._get_document_or_404(doc_id)

        doc.is_deleted = True
        doc.deleted_at = datetime.now(timezone.utc)
        doc.deleted_by = actor_id

        # Optionally signal storage layer (no-op for local backend)
        self.storage.soft_delete(doc.file_path)

        await log_event(
            self.db,
            action=AuditActionEnum.DELETE,
            module=AuditModuleEnum.SOP,
            user_id=actor_id,
            target_id=doc.id,
            description=(
                f"Soft-deleted: '{doc.title}' v{doc.version_number} "
                f"(section: {doc.section.name if doc.section else '?'}). "
                f"File retained on disk."
            ),
            ip_address=ip,
        )

    # =========================================================================
    # AUDIT TRAIL
    # =========================================================================

    async def get_logs(self, doc_id: uuid.UUID) -> list[AuditLog]:
        """Return the full audit trail for a document, newest first."""
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.target_id == doc_id)
            .order_by(AuditLog.created_at.desc())
        )
        return result.scalars().all()
