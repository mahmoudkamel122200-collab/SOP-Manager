"""
Pydantic v2 schemas for all API request/response models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.models import (
    AuditActionEnum,
    AuditModuleEnum,
    DocumentStatusEnum,
    ItemStatusEnum,
    PermissionLevelEnum,
)

T = TypeVar("T")


# =============================================================================
# Standard API Envelope
# =============================================================================

class SuccessResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: T


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    code: str


class PaginatedResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: List[T]
    total: int
    page: int
    page_size: int


# =============================================================================
# Authentication Schemas
# =============================================================================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["admin"])
    password: str = Field(..., min_length=8, examples=["Admin@1234"])


class SelectSectionRequest(BaseModel):
    section_id: uuid.UUID


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


# =============================================================================
# Role Schemas
# =============================================================================

class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# User Schemas
# =============================================================================

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=150)
    role_id: uuid.UUID

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=150)
    role_id: Optional[uuid.UUID] = None


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    full_name: Optional[str]
    role: RoleOut
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class UserBlockRequest(BaseModel):
    is_active: bool


# =============================================================================
# Section Schemas
# =============================================================================

class SectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class SectionOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSectionAssignRequest(BaseModel):
    user_id: uuid.UUID
    section_id: uuid.UUID
    permission_level: PermissionLevelEnum = PermissionLevelEnum.READ


class UserSectionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    section_id: uuid.UUID
    permission_level: PermissionLevelEnum
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Document Schemas
# =============================================================================

class DocumentCreateRequest(BaseModel):
    section_id: uuid.UUID
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    version: str = Field(default="1.0", pattern=r"^\d+\.\d+(\.\d+)?$")
    # file is uploaded separately via multipart/form-data


class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    status: Optional[DocumentStatusEnum] = None


class DocumentOut(BaseModel):
    id: uuid.UUID
    section_id: uuid.UUID
    section_name: Optional[str] = None
    title: str
    description: Optional[str]
    file_path: str
    version: str
    uploaded_by: uuid.UUID
    uploader_name: Optional[str] = None
    status: DocumentStatusEnum
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Audit Log Schemas
# =============================================================================

class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: AuditActionEnum
    module: AuditModuleEnum
    target_id: Optional[uuid.UUID]
    description: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Warehouse Schemas
# =============================================================================

class LocationOut(BaseModel):
    id: uuid.UUID
    warehouse_name: str
    rack: str
    shelf: str
    position: str
    location_code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ItemCreateRequest(BaseModel):
    item_code: str = Field(..., pattern=r"^[A-Z]{2}-\d{6}$", examples=["BG-000123"])
    material_name: str = Field(..., min_length=2, max_length=200)
    quantity: float = Field(..., ge=0)
    unit: str = Field(..., min_length=1, max_length=20, examples=["KG"])
    location_id: uuid.UUID


class ItemOut(BaseModel):
    id: uuid.UUID
    item_code: str
    material_name: str
    quantity: float
    unit: str
    location: LocationOut
    status: ItemStatusEnum
    created_at: datetime

    model_config = {"from_attributes": True}


class MoveItemRequest(BaseModel):
    to_location_id: uuid.UUID
    notes: Optional[str] = Field(None, max_length=500)


class MovementLogOut(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    from_location: Optional[LocationOut]
    to_location: LocationOut
    moved_by: uuid.UUID
    mover_name: Optional[str] = None
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
