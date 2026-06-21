"""
schemas/warehouse.py

Pydantic v2 models for Warehouse endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.warehouse import ItemStatusEnum


class LocationOut(BaseModel):
    id: uuid.UUID
    warehouse_name: str
    rack: str
    shelf: str
    position: str
    location_code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LocationCreateRequest(BaseModel):
    warehouse_name: str = Field(..., min_length=1, max_length=100, examples=["Warehouse A"])
    rack: str = Field(..., min_length=1, max_length=20, examples=["R01"])
    shelf: str = Field(..., min_length=1, max_length=20, examples=["S03"])
    position: str = Field(..., min_length=1, max_length=20, examples=["P05"])


class LocationSearchInfo(BaseModel):
    warehouse: str
    rack: str
    shelf: str
    position: str


class ItemSearchResponse(BaseModel):
    id: uuid.UUID
    item_code: str
    material: str
    quantity: float
    location: LocationSearchInfo


class ItemCreateRequest(BaseModel):
    item_code: str = Field(
        ...,
        pattern=r"^[A-Z]{2}-\d{6}$",
        examples=["BG-000123"],
        description="Format: 2 uppercase letters + dash + 6 digits",
    )
    material_name: str = Field(..., min_length=2, max_length=200)
    quantity: float = Field(..., ge=0, description="Must be non-negative")
    unit: str = Field(..., min_length=1, max_length=20, examples=["KG", "L", "PCS"])
    location_id: uuid.UUID


class ItemCreateWithNewLocationRequest(BaseModel):
    """Create an item AND its location in a single transaction."""
    item_code: str = Field(
        ...,
        pattern=r"^[A-Z]{2}-\d{6}$",
        examples=["BG-000123"],
        description="Format: 2 uppercase letters + dash + 6 digits",
    )
    material_name: str = Field(..., min_length=2, max_length=200)
    quantity: float = Field(..., ge=0, description="Must be non-negative")
    unit: str = Field(..., min_length=1, max_length=20, examples=["KG", "L", "PCS"])
    warehouse_name: str = Field(..., min_length=1, max_length=100)
    rack: str = Field(..., min_length=1, max_length=20)
    shelf: str = Field(..., min_length=1, max_length=20)
    position: str = Field(..., min_length=1, max_length=20)


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
    to_location_id: uuid.UUID = Field(..., alias="new_location_id", validation_alias="new_location_id")
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
