"""
schemas/__init__.py

Re-export all schemas for convenient imports.
"""

from app.schemas.auth import (  # noqa: F401
    LoginRequest,
    MeResponse,
    RefreshRequest,
    SelectSectionRequest,
    SectionSelectResponse,
    TokenPair,
)
from app.schemas.user import (  # noqa: F401
    RoleOut,
    UserBlockRequest,
    UserCreateRequest,
    UserOut,
    UserUpdateRequest,
)
from app.schemas.section import (  # noqa: F401
    SectionCreateRequest,
    SectionOut,
    UserSectionAssignRequest,
    UserSectionOut,
)
from app.schemas.document import AuditLogOut, DocumentOut, DocumentUpdateStatusRequest  # noqa: F401
from app.schemas.warehouse import (  # noqa: F401
    ItemCreateRequest,
    ItemOut,
    LocationOut,
    MoveItemRequest,
    MovementLogOut,
)
