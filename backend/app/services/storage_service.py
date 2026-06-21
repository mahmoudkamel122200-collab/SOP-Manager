"""
services/storage_service.py

File storage abstraction layer.

Design goals:
  1. MVP runs entirely on local disk — zero external dependencies.
  2. Swapping to S3 (or MinIO) requires ONLY replacing LocalStorageBackend
     with S3StorageBackend — zero changes to document_service.py.
  3. File naming is deterministic and human-readable:
       {section}/{slugified_title}_v{version}_{epoch}.{ext}
  4. Files are NEVER deleted. The soft-delete design means only
     DB records are hidden; files remain for audit/recovery.

To switch to S3:
  1. pip install boto3
  2. Implement S3StorageBackend below
  3. Change get_storage_backend() to return S3StorageBackend(...)
  4. Set STORAGE_BACKEND=s3 in .env
"""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# ── Constants ─────────────────────────────────────────────────────────────────
UPLOAD_ROOT = Path(settings.UPLOAD_DIR)
MAX_BYTES   = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXT = set(ext.lower() for ext in settings.ALLOWED_EXTENSIONS)

MIME_MAP = {
    "pdf":  "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "txt":  "text/plain",
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
}


def _slugify(text: str) -> str:
    """Convert a title to a safe filesystem slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:60]   # cap length


def _section_dir(section_name: str) -> str:
    """Convert a section name to a safe directory name."""
    return re.sub(r"[^\w]+", "_", section_name.lower()).strip("_")


# =============================================================================
# Abstract interface — defines the contract for any storage backend
# =============================================================================

class StorageBackend(ABC):
    """Protocol that every storage backend must implement."""

    @abstractmethod
    async def save(
        self,
        *,
        content: bytes,
        title: str,
        version_number: int,
        section_name: str,
        extension: str,
    ) -> tuple[str, str]:
        """
        Persist the file and return (relative_path, stored_filename).
        relative_path is stored in DB; stored_filename is the on-disk name.
        """
        ...

    @abstractmethod
    def resolve(self, relative_path: str) -> Path:
        """Return the absolute OS path for a stored file."""
        ...

    @abstractmethod
    def public_url(self, relative_path: str) -> str:
        """Return the URL that clients use to download the file."""
        ...

    def soft_delete(self, relative_path: str) -> None:
        """
        Called on document soft-delete. Default is a no-op —
        we intentionally keep files for audit purposes.
        Override if you want to move files to a 'deleted/' prefix on S3.
        """


# =============================================================================
# LOCAL DISK BACKEND (MVP)
# =============================================================================

class LocalStorageBackend(StorageBackend):
    """
    Stores files on the local filesystem under UPLOAD_ROOT.

    Directory layout:
      UPLOAD_ROOT/
        {section_slug}/
          {title_slug}_v{version}_{epoch}.{ext}

    Example:
      uploads/documents/
        production/
          machine_safety_sop_v1_1750424400.pdf
          machine_safety_sop_v2_1750511000.pdf
        warehouse/
          bin_labelling_procedure_v1_1750500000.pdf
    """

    def __init__(self, root: Path = UPLOAD_ROOT) -> None:
        self.root = root

    async def save(
        self,
        *,
        content: bytes,
        title: str,
        version_number: int,
        section_name: str,
        extension: str,
    ) -> tuple[str, str]:
        section_slug = _section_dir(section_name)
        title_slug   = _slugify(title)
        epoch        = int(time.time())
        filename     = f"{title_slug}_v{version_number}_{epoch}.{extension}"

        dest_dir = self.root / section_slug
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / filename
        dest_path.write_bytes(content)

        # Relative path stored in DB: "production/filename.pdf"
        relative = f"{section_slug}/{filename}"
        return relative, filename

    def resolve(self, relative_path: str) -> Path:
        return self.root / relative_path

    def public_url(self, relative_path: str) -> str:
        """
        Returns the API download URL.
        The /documents/{id}/download endpoint serves the actual bytes.
        """
        return f"/api/v1/documents/files/{relative_path}"

    def soft_delete(self, relative_path: str) -> None:
        # Intentional no-op: files are never removed from disk.
        pass


# =============================================================================
# SUPABASE STORAGE BACKEND
# =============================================================================

class SupabaseStorageBackend(StorageBackend):
    """
    Supabase Storage backend.
    Install: pip install supabase

    To activate:
      1. Set STORAGE_BACKEND=supabase in .env
      2. Set SUPABASE_URL and SUPABASE_KEY in .env
      3. Create a public bucket in Supabase called "documents" (or set SUPABASE_BUCKET)
    """

    def __init__(self, url: str, key: str, bucket: str = "documents"):
        from supabase import create_client, Client
        self.bucket = bucket
        self.client: Client = create_client(url, key)

    async def save(self, *, content: bytes, title: str, version_number: int, section_name: str, extension: str) -> tuple[str, str]:
        section_slug = _section_dir(section_name)
        title_slug   = _slugify(title)
        epoch        = int(time.time())
        filename     = f"{title_slug}_v{version_number}_{epoch}.{extension}"

        # Relative path stored in DB: "production/filename.pdf"
        relative = f"{section_slug}/{filename}"

        mime = MIME_MAP.get(extension.lower(), "application/octet-stream")
        try:
            self.client.storage.from_(self.bucket).upload(
                path=relative,
                file=content,
                file_options={"content-type": mime}
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to Supabase Storage: {str(e)}. Please ensure the '{self.bucket}' bucket exists and is public."
            )

        return relative, filename

    def resolve(self, relative_path: str) -> Path:
        raise NotImplementedError("Supabase files don't have a local path.")

    def public_url(self, relative_path: str) -> str:
        """Returns the public URL for the file from Supabase Storage."""
        return self.client.storage.from_(self.bucket).get_public_url(relative_path)


# =============================================================================
# VALIDATION UTILITIES (storage-agnostic)
# =============================================================================

def validate_upload_file(file: UploadFile) -> tuple[str, str]:
    """
    Validate the uploaded file before reading content.
    Returns (extension, mime_type).
    Raises HTTPException on invalid file.
    """
    filename = file.filename or ""
    if "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File must have an extension.",
        )

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '.{ext}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXT))}",
        )

    mime = MIME_MAP.get(ext, "application/octet-stream")
    return ext, mime


async def read_and_validate_content(file: UploadFile) -> bytes:
    """
    Read file bytes and validate size.
    Raises HTTPException if file exceeds MAX_UPLOAD_SIZE_MB.
    """
    content = await file.read()
    await file.seek(0)   # reset pointer in case caller needs to re-read

    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File is too large ({len(content) / (1024*1024):.1f} MB). "
                f"Maximum allowed: {settings.MAX_UPLOAD_SIZE_MB} MB."
            ),
        )
    return content


# =============================================================================
# DEPENDENCY: get_storage_backend()
# =============================================================================

_backend: Optional[StorageBackend] = None


def get_storage_backend() -> StorageBackend:
    """
    FastAPI / application dependency.
    Returns the configured storage backend singleton.

    Swap backends by changing settings.STORAGE_BACKEND:
      "local"    → LocalStorageBackend  (default)
      "supabase" → SupabaseStorageBackend
    """
    global _backend
    if _backend is None:
        backend_name = getattr(settings, "STORAGE_BACKEND", "local").lower()
        if backend_name == "supabase":
            import os
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_KEY", "")
            bucket = os.getenv("SUPABASE_BUCKET", "documents")
            _backend = SupabaseStorageBackend(url=url, key=key, bucket=bucket)
        else:
            _backend = LocalStorageBackend(UPLOAD_ROOT)
    return _backend
