"""
schemas/auth.py

Pydantic v2 models for Authentication endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# REQUEST MODELS
# =============================================================================

class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        examples=["admin"],
        description="The user's login handle",
    )
    password: str = Field(
        ...,
        min_length=8,
        examples=["Admin@1234"],
        description="Plain-text password (transmitted over HTTPS only)",
    )


class SelectSectionRequest(BaseModel):
    section_id: uuid.UUID = Field(
        ...,
        description="UUID of the section to activate",
        examples=["00000000-0000-0000-0002-000000000003"],
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        description="The long-lived refresh token received at login",
    )


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class TokenPair(BaseModel):
    """Access + refresh token pair returned on login or refresh."""
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int  # seconds until access token expires


class SectionSummary(BaseModel):
    """Brief section info embedded in login/me responses."""
    id:               str
    name:             str
    description:      Optional[str]
    permission_level: str  # READ | WRITE | ADMIN


class UserSummary(BaseModel):
    """User identity embedded in login response."""
    id:        str
    username:  str
    email:     str
    full_name: Optional[str]
    role:      str


class LoginResponse(BaseModel):
    """Full login response — everything the frontend needs to bootstrap the app."""
    access_token:              str
    refresh_token:             str
    token_type:                str = "bearer"
    expires_in:                int
    user:                      UserSummary
    available_sections:        list[SectionSummary]
    requires_section_selection: bool


class SectionSelectResponse(BaseModel):
    """Response from POST /auth/select-section."""
    access_token:     str
    token_type:       str = "bearer"
    section:          dict[str, Any]
    permission_level: str
    message:          str


class MeResponse(BaseModel):
    """Current user profile — returned by GET /auth/me."""
    id:               str
    username:         str
    email:            str
    full_name:        Optional[str]
    role:             str
    is_active:        bool
    last_login:       Optional[str]
    active_section_id: Optional[str]
    available_sections: list[SectionSummary]
    requires_section_selection: bool

    model_config = {"from_attributes": True}
