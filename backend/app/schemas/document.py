"""
schemas/document.py

Pydantic v2 models for SOP Document endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.document import DocumentStatusEnum


# =============================================================================
# NESTED MODELS
# =============================================================================

class SectionBrief(BaseModel):
    id:   uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class UploaderBrief(BaseModel):
    id:        uuid.UUID
    username:  str
    full_name: Optional[str]

    model_config = {"from_attributes": True}


# =============================================================================
# DOCUMENT OUTPUT  (full detail — used for single-doc fetch)
# =============================================================================

class DocumentOut(BaseModel):
    """Full document metadata — returned by GET /documents/{id}."""
    id:               uuid.UUID
    title:            str
    description:      Optional[str]
    version_number:   int
    version_label:    Optional[str]
    section:          SectionBrief
    uploaded_by:      uuid.UUID
    uploader:         Optional[UploaderBrief]
    status:           DocumentStatusEnum
    file_name:        str
    file_size_bytes:  Optional[int]
    mime_type:        Optional[str]
    download_url:     Optional[str]    # populated by router from storage backend
    created_at:       datetime
    is_deleted:       bool

    model_config = {"from_attributes": True}


# =============================================================================
# DOCUMENT SUMMARY  (list item — omits heavy fields)
# =============================================================================

class DocumentSummary(BaseModel):
    """Lightweight doc info for list endpoints."""
    id:              uuid.UUID
    title:           str
    version_number:  int
    version_label:   Optional[str]
    section_id:      uuid.UUID
    section_name:    Optional[str]
    status:          DocumentStatusEnum
    uploader_name:   Optional[str]
    file_name:       str
    file_size_bytes: Optional[int]
    created_at:      datetime

    model_config = {"from_attributes": True}


# =============================================================================
# UPDATE REQUEST
# =============================================================================

class DocumentUpdateRequest(BaseModel):
    """Body for PATCH /documents/{id}."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    section_id: Optional[uuid.UUID] = None


# =============================================================================
# STATUS UPDATE REQUEST
# =============================================================================

class DocumentUpdateStatusRequest(BaseModel):
    """Body for PATCH /documents/{id}/status."""
    status: DocumentStatusEnum = Field(
        ...,
        description="New lifecycle status. Valid transitions are enforced server-side.",
    )


# =============================================================================
# AUDIT LOG OUTPUT
# =============================================================================

class AuditLogOut(BaseModel):
    """Single audit trail entry."""
    id:          uuid.UUID
    user_id:     Optional[uuid.UUID]
    action:      str
    module:      str
    target_id:   Optional[uuid.UUID]
    description: Optional[str]
    ip_address:  Optional[str]
    created_at:  datetime

    model_config = {"from_attributes": True}


# =============================================================================
# PAGINATED RESPONSE HELPERS
# =============================================================================

class PaginatedDocuments(BaseModel):
    """Paginated list of document summaries."""
    documents:  list[DocumentSummary]
    total:      int
    page:       int
    page_size:  int
    pages:      int


class VersionHistoryResponse(BaseModel):
    """All versions of a document."""
    title:        str
    section_name: str
    versions:     list[DocumentSummary]
