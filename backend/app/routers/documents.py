"""
routers/documents.py

SOP Document Management — HTTP endpoints.
All business logic lives in DocumentService. This file is a pure HTTP adapter.

Endpoints:
  GET    /api/v1/documents                      Admin: list all documents
  GET    /api/v1/documents/section/{section_id} List section docs (search, filter, paginate)
  POST   /api/v1/documents                      Upload new doc (Admin only, multipart)
  GET    /api/v1/documents/{id}                 Get metadata + download URL
  GET    /api/v1/documents/{id}/download        Stream the actual file
  GET    /api/v1/documents/{id}/versions        Version history for same title
  PATCH  /api/v1/documents/{id}/status          Lifecycle transition
  DELETE /api/v1/documents/{id}                 Soft delete (Admin only)
  GET    /api/v1/documents/{id}/logs            Audit trail (Admin only)

Security:
  All endpoints require a valid JWT.
  Upload / delete / status / logs → Admin only.
  Section list → active section in token must match requested section (Employee)
  Single doc  → user must have access to the doc's section (Employee)
"""

from __future__ import annotations

import math
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_token, require_role
from app.middleware.auth_middleware import require_section_permission
from app.models.document import DocumentStatusEnum
from app.models.section import PermissionLevelEnum
from app.schemas.document import (
    AuditLogOut,
    DocumentOut,
    DocumentSummary,
    DocumentUpdateRequest,
    DocumentUpdateStatusRequest,
    PaginatedDocuments,
    SectionBrief,
    UploaderBrief,
    VersionHistoryResponse,
)
from app.services.document_service import DocumentService
from app.services.storage_service import get_storage_backend

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ip(r: Request) -> str:
    fwd = r.headers.get("X-Forwarded-For")
    return fwd.split(",")[0].strip() if fwd else (
        r.client.host if r.client else "unknown"
    )


def _svc(db: AsyncSession) -> DocumentService:
    return DocumentService(db, get_storage_backend())


def _to_summary(doc, storage=None) -> dict:
    """Convert a Document ORM object to a DocumentSummary dict."""
    return DocumentSummary(
        id=doc.id,
        title=doc.title,
        version_number=doc.version_number,
        version_label=doc.version_label,
        sections=[SectionBrief(id=s.id, name=s.name) for s in doc.sections],
        status=doc.status,
        uploader_name=doc.uploader.full_name or doc.uploader.username if doc.uploader else None,
        file_name=doc.file_name,
        file_size_bytes=doc.file_size_bytes,
        created_at=doc.created_at,
    ).model_dump(mode="json")


def _to_detail(doc, storage) -> dict:
    """Convert a Document ORM object to a full DocumentOut dict."""
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        description=doc.description,
        version_number=doc.version_number,
        version_label=doc.version_label,
        sections=[SectionBrief(id=s.id, name=s.name) for s in doc.sections],
        uploaded_by=doc.uploaded_by,
        uploader=UploaderBrief(
            id=doc.uploader.id,
            username=doc.uploader.username,
            full_name=doc.uploader.full_name,
        ) if doc.uploader else None,
        status=doc.status,
        file_name=doc.file_name,
        file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type,
        download_url=storage.public_url(doc.file_path) if storage else None,
        created_at=doc.created_at,
        is_deleted=doc.is_deleted,
    ).model_dump(mode="json")


# =============================================================================
# GET /documents  —  Admin: list ALL documents across all sections
# =============================================================================

@router.get(
    "",
    summary="[Admin] List all documents across all sections",
    description="""
Returns a paginated list of all documents in the system.

Supports:
- `search` — full-text search on title and description
- `status`  — filter by lifecycle status
- `section_id` — narrow to a specific section
- `page` / `page_size` — pagination
    """,
)
async def list_all_documents(
    search:       str | None              = Query(None, description="Search title/description"),
    status_filter: DocumentStatusEnum | None = Query(None, alias="status"),
    section_id:   uuid.UUID | None        = Query(None),
    page:         int                     = Query(1, ge=1),
    page_size:    int                     = Query(20, ge=1, le=100),
    _payload:     dict                    = Depends(require_role("ADMIN")),
    db:           AsyncSession            = Depends(get_db),
):
    docs, total = await _svc(db).list_all(
        search=search,
        status_filter=status_filter,
        section_id=section_id,
        page=page,
        page_size=page_size,
    )
    return {
        "status": "success",
        "data": PaginatedDocuments(
            documents=[_to_summary(d) for d in docs],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        ).model_dump(mode="json"),
    }


# =============================================================================
# GET /documents/section/{section_id}  —  List section documents
# =============================================================================

@router.get(
    "/section/{section_id}",
    summary="List SOP documents in a section",
    description="""
Returns all active documents in the specified section.

**Access control:**
- ADMIN → can query any section
- EMPLOYEE → token must have `section_id` claim matching this section
  (call `POST /auth/select-section` first)

Supports search + status filter + pagination.
    """,
)
async def list_section_documents(
    section_id:       uuid.UUID,
    request:          Request,
    search:           str | None               = Query(None),
    status_filter:    DocumentStatusEnum | None = Query(None, alias="status"),
    include_archived: bool                      = Query(False),
    page:             int                       = Query(1, ge=1),
    page_size:        int                       = Query(20, ge=1, le=100),
    token_payload:    dict                      = Depends(get_current_token),
    db:               AsyncSession              = Depends(get_db),
):
    # For employees, the token's active section must match the requested section
    role = token_payload.get("role", "")
    if role != "ADMIN":
        active_section = token_payload.get("section_id")
        if active_section and str(section_id) != active_section:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Your active section does not match this section. "
                    "Call POST /auth/select-section to switch sections."
                ),
            )

    docs, total = await _svc(db).list_by_section(
        section_id=section_id,
        user_id=uuid.UUID(token_payload["sub"]),
        role=role,
        search=search,
        status_filter=status_filter,
        include_archived=include_archived,
        page=page,
        page_size=page_size,
    )

    return {
        "status": "success",
        "data": PaginatedDocuments(
            documents=[_to_summary(d) for d in docs],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        ).model_dump(mode="json"),
    }


# =============================================================================
# POST /documents  —  Upload new SOP document (Admin only)
# =============================================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Upload a new SOP document",
    description="""
Upload a new SOP document via multipart/form-data.

**Auto-versioning:**
If a document with the same title already exists in the same section,
the version number is automatically incremented. You do NOT need to
specify the version — the server computes it.

**File naming (on disk):**
`{section}/{title_slug}_v{version}_{timestamp}.{ext}`

**Allowed file types:** PDF, DOCX, XLSX, PPTX, TXT (configurable)

**Max size:** Configurable via MAX_UPLOAD_SIZE_MB in .env (default 20 MB)
    """,
)
async def upload_document(
    request:       Request,
    section_ids:   str          = Form(..., description="Comma-separated UUIDs of the target sections"),
    title:         str          = Form(..., min_length=3, max_length=255, description="Document title"),
    description:   str | None   = Form(None, description="Optional description or summary"),
    version_label: str | None   = Form(None, max_length=50, description="Optional human label, e.g. 'Rev. A'"),
    file:          UploadFile   = File(..., description="The SOP file to upload"),
    token_payload: dict         = Depends(require_role("ADMIN")),
    db:            AsyncSession = Depends(get_db),
):
    storage = get_storage_backend()
    svc     = DocumentService(db, storage)

    # Parse section_ids
    parsed_section_ids = []
    for sid in section_ids.split(','):
        sid = sid.strip()
        if sid:
            parsed_section_ids.append(uuid.UUID(sid))

    if not parsed_section_ids:
        raise HTTPException(status_code=400, detail="At least one section must be provided")

    doc = await svc.upload(
        section_ids=parsed_section_ids,
        title=title,
        description=description,
        version_label=version_label,
        file=file,
        uploader_id=uuid.UUID(token_payload["sub"]),
        ip=_ip(request),
    )

    return {
        "status": "success",
        "data":   _to_detail(doc, storage),
    }


# =============================================================================
# GET /documents/{id}  —  Get document metadata
# =============================================================================

@router.get(
    "/{doc_id}",
    summary="Get SOP document metadata",
    description="""
Returns full document metadata including a `download_url`.

**Access control:**
- ADMIN → always allowed
- EMPLOYEE → must have access to the document's section via `user_sections`

Every successful call is logged as an **OPEN_DOCUMENT** audit event.
    """,
)
async def get_document(
    doc_id:        uuid.UUID,
    request:       Request,
    token_payload: dict         = Depends(get_current_token),
    db:            AsyncSession = Depends(get_db),
):
    storage = get_storage_backend()
    doc     = await DocumentService(db, storage).get(
        doc_id=doc_id,
        user_id=uuid.UUID(token_payload["sub"]),
        role=token_payload.get("role", ""),
        ip=_ip(request),
    )
    return {"status": "success", "data": _to_detail(doc, storage)}


# =============================================================================
# GET /documents/{id}/download  —  Stream the actual file
# =============================================================================

@router.get(
    "/{doc_id}/download",
    summary="Download the actual SOP file",
    description="""
Streams the binary file to the client.

Responds with the correct Content-Type header so the browser can display
PDFs inline and trigger appropriate viewers for other file types.

Logs an **OPEN_DOCUMENT** audit event on every download.
    """,
)
async def download_document(
    doc_id:        uuid.UUID,
    request:       Request,
    token_payload: dict         = Depends(get_current_token),
    db:            AsyncSession = Depends(get_db),
):
    storage = get_storage_backend()
    path_or_url, filename, mime = await DocumentService(db, storage).resolve_for_download(
        doc_id=doc_id,
        user_id=uuid.UUID(token_payload["sub"]),
        role=token_payload.get("role", ""),
        ip=_ip(request),
    )
    
    if isinstance(path_or_url, str) and (path_or_url.startswith("http://") or path_or_url.startswith("https://")):
        return RedirectResponse(path_or_url)
        
    return FileResponse(
        path=str(path_or_url),
        media_type=mime,
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# =============================================================================
# GET /documents/{id}/versions  —  Version history
# =============================================================================

@router.get(
    "/{doc_id}/versions",
    summary="Get all versions of a document",
    description="""
Returns all uploaded versions of the document identified by `doc_id`,
ordered newest-first. All versions share the same title + section.
    """,
)
async def document_versions(
    doc_id:        uuid.UUID,
    token_payload: dict         = Depends(get_current_token),
    db:            AsyncSession = Depends(get_db),
):
    storage  = get_storage_backend()
    versions = await DocumentService(db, storage).get_versions(
        doc_id=doc_id,
        user_id=uuid.UUID(token_payload["sub"]),
        role=token_payload.get("role", ""),
    )

    if not versions:
        return {"status": "success", "data": {"title": "", "section_name": "", "versions": []}}

    first = versions[0]
    return {
        "status": "success",
        "data": VersionHistoryResponse(
            title=first.title,
            section_name=first.section.name if first.section else "",
            versions=[_to_summary(v) for v in versions],
        ).model_dump(mode="json"),
    }


# =============================================================================
# PATCH /documents/{id}/status  —  Lifecycle transition
# =============================================================================

@router.patch(
    "/{doc_id}/status",
    summary="[Admin] Update document lifecycle status",
    description="""
Transition a document through its lifecycle.

Valid transitions:
```
DRAFT → UNDER_REVIEW → APPROVED → ARCHIVED
UNDER_REVIEW → REJECTED → DRAFT
```

Invalid transitions are rejected with **400 Bad Request**.
    """,
)
async def update_document_status(
    doc_id:        uuid.UUID,
    request:       Request,
    body:          DocumentUpdateStatusRequest,
    token_payload: dict         = Depends(require_role("ADMIN")),
    db:            AsyncSession = Depends(get_db),
):
    doc = await _svc(db).update_status(
        doc_id=doc_id,
        new_status=body.status,
        actor_id=uuid.UUID(token_payload["sub"]),
        ip=_ip(request),
    )
    return {
        "status": "success",
        "data":   {"id": str(doc.id), "title": doc.title, "status": doc.status.value},
    }


# =============================================================================
# PATCH /documents/{id}  —  Update Document Metadata
# =============================================================================

@router.patch(
    "/{doc_id}",
    summary="[Admin] Update document metadata",
    description="""
Update the basic metadata (title, description, section_ids) of a document.
    """,
)
async def update_document_metadata(
    doc_id:        uuid.UUID,
    request:       Request,
    body:          DocumentUpdateRequest,
    token_payload: dict         = Depends(require_role("ADMIN")),
    db:            AsyncSession = Depends(get_db),
):
    storage = get_storage_backend()
    doc = await _svc(db).update(
        doc_id=doc_id,
        title=body.title,
        description=body.description,
        section_ids=body.section_ids,
        actor_id=uuid.UUID(token_payload["sub"]),
        ip=_ip(request),
    )
    return {
        "status": "success",
        "data":   _to_detail(doc, storage),
    }


# =============================================================================
# DELETE /documents/{id}  —  Soft delete (Admin only)
# =============================================================================

@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_200_OK,
    summary="[Admin] Soft-delete a document",
    description="""
Marks the document as deleted (`is_deleted=True`).

**Files are never physically removed** — they remain on disk for audit
and recovery purposes. Only the database record is hidden from queries.

The action is logged as a **DELETE_DOCUMENT** audit event.

To permanently remove a file, a separate admin-only data retention
process must be implemented outside this API.
    """,
)
async def delete_document(
    doc_id:        uuid.UUID,
    request:       Request,
    token_payload: dict         = Depends(require_role("ADMIN")),
    db:            AsyncSession = Depends(get_db),
):
    await _svc(db).soft_delete(
        doc_id=doc_id,
        actor_id=uuid.UUID(token_payload["sub"]),
        ip=_ip(request),
    )
    return {
        "status": "success",
        "data": {
            "message": "Document has been soft-deleted. File retained on storage.",
            "id": str(doc_id),
        },
    }


# =============================================================================
# GET /documents/{id}/logs  —  Audit trail (Admin only)
# =============================================================================

@router.get(
    "/{doc_id}/logs",
    summary="[Admin] Get document audit trail",
    description="""
Returns the full audit trail for a document — every UPLOAD, OPEN,
STATUS CHANGE, and DELETE event, newest first.
    """,
)
async def document_audit_logs(
    doc_id:  uuid.UUID,
    _:       dict         = Depends(require_role("ADMIN")),
    db:      AsyncSession = Depends(get_db),
):
    logs = await _svc(db).get_logs(doc_id)
    return {
        "status": "success",
        "data": {
            "document_id": str(doc_id),
            "logs": [
                AuditLogOut.model_validate(log).model_dump(mode="json")
                for log in logs
            ],
        },
    }
