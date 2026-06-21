"""
schemas/section.py

Pydantic v2 models for Section endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.section import PermissionLevelEnum


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
