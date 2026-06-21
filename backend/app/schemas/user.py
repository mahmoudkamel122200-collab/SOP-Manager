"""
schemas/user.py

Pydantic v2 models for User and Role endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Role ──────────────────────────────────────────────────────────────────────

class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User ──────────────────────────────────────────────────────────────────────

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
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=150)
    role_id: Optional[uuid.UUID] = None


class UserBlockRequest(BaseModel):
    is_active: bool


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
