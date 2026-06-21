"""
models/__init__.py

Central import point for all ORM models.
Alembic's env.py imports Base from here so all tables are auto-discovered.

Import ORDER matters — parent tables before child tables to resolve FK references.
"""

from app.models.base import Base  # noqa: F401

# IAM
from app.models.role import Role  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.section import Section, UserSection, PermissionLevelEnum  # noqa: F401

# SOP
from app.models.document import Document, DocumentStatusEnum  # noqa: F401

# Warehouse
from app.models.warehouse import Location, Item, MovementLog, ItemStatusEnum  # noqa: F401

# Cross-cutting
from app.models.audit_log import AuditLog, AuditActionEnum, AuditModuleEnum  # noqa: F401

__all__ = [
    "Base",
    # IAM
    "Role", "User", "Section", "UserSection", "PermissionLevelEnum",
    # SOP
    "Document", "DocumentStatusEnum",
    # Warehouse
    "Location", "Item", "MovementLog", "ItemStatusEnum",
    # Audit
    "AuditLog", "AuditActionEnum", "AuditModuleEnum",
]
