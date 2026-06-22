"""
routers/warehouse.py — Warehouse endpoints, delegates to WarehouseService.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.middleware.auth_middleware import require_section_permission
from app.models.section import PermissionLevelEnum
from app.schemas.warehouse import (
    ItemCreateRequest, ItemCreateWithNewLocationRequest, ItemOut, LocationOut,
    MoveItemRequest, MovementLogOut,
    LocationCreateRequest, LocationSearchInfo, ItemSearchResponse
)
from app.services.warehouse_service import WarehouseService
from app.utils.responses import paginated_response, success_response

router = APIRouter()

_read  = Depends(require_section_permission(PermissionLevelEnum.READ))
_write = Depends(require_section_permission(PermissionLevelEnum.WRITE))


def _ip(r: Request) -> str:
    fwd = r.headers.get("X-Forwarded-For")
    return fwd.split(",")[0].strip() if fwd else (r.client.host if r.client else "unknown")


def _item_out(item) -> dict:
    return ItemOut(
        id=item.id,
        item_code=item.item_code,
        material_name=item.material_name,
        quantity=float(item.quantity),
        unit=item.unit,
        location=LocationOut.model_validate(item.location),
        status=item.status,
        created_at=item.created_at,
    ).model_dump(mode="json")


def _item_search_out(item) -> dict:
    """Format matching Feature 3 requirements exactly."""
    return ItemSearchResponse(
        id=item.id,
        item_code=item.item_code,
        material=item.material_name,
        quantity=float(item.quantity),
        location=LocationSearchInfo(
            warehouse=item.location.warehouse_name,
            rack=item.location.rack,
            shelf=item.location.shelf,
            position=item.location.position,
        )
    ).model_dump(mode="json")


def _movement_history_out(m) -> dict:
    """Format matching Feature 5 requirements exactly."""
    return {
        "from": m.from_loc.location_code if m.from_loc else None,
        "to": m.to_loc.location_code,
        "moved_by": m.mover.full_name or m.mover.username if m.mover else "System",
        "date": m.created_at.isoformat(),
    }


# =============================================================================
# WAREHOUSE LOCATION MANAGEMENT (Feature 1)
# =============================================================================

@router.get("/locations", dependencies=[_read])
async def list_locations(db: AsyncSession = Depends(get_db)):
    locs = await WarehouseService(db).list_locations()
    return success_response(data=[LocationOut.model_validate(l).model_dump(mode="json") for l in locs])


@router.post("/locations", status_code=status.HTTP_201_CREATED)
async def create_location(
    body: LocationCreateRequest,
    request: Request,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    loc = await WarehouseService(db).create_location(
        body, uuid.UUID(token_payload["sub"]), _ip(request)
    )
    return success_response(data=LocationOut.model_validate(loc).model_dump(mode="json"), status_code=201)


# =============================================================================
# ITEM / BAG MANAGEMENT (Feature 2)
# =============================================================================

@router.get("/items", dependencies=[_read])
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await WarehouseService(db).list_items(page=page, page_size=page_size, status_filter=status_filter)
    return success_response(data=[_item_out(i) for i in items])

@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(
    body: ItemCreateRequest,
    request: Request,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    item = await WarehouseService(db).create_item(
        body, uuid.UUID(token_payload["sub"]), _ip(request)
    )
    return success_response(data=_item_out(item), status_code=201)


@router.post("/items/with-location", status_code=status.HTTP_201_CREATED)
async def create_item_with_location(
    body: ItemCreateWithNewLocationRequest,
    request: Request,
    token_payload: dict = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new item AND its location in a single transaction."""
    item = await WarehouseService(db).create_item_with_location(
        body, uuid.UUID(token_payload["sub"]), _ip(request)
    )
    return success_response(data=_item_out(item), status_code=201)


# =============================================================================
# SEARCH ITEM LOCATION (Feature 3)
# =============================================================================

@router.get("/items/{item_code}")
async def get_item(
    item_code: str,
    request: Request,
    token_payload: dict = Depends(require_section_permission(PermissionLevelEnum.READ)),
    db: AsyncSession = Depends(get_db),
):
    item = await WarehouseService(db).get_by_code(
        item_code, uuid.UUID(token_payload["sub"]), _ip(request)
    )
    return success_response(data=_item_search_out(item))


# =============================================================================
# MOVE ITEM (Feature 4)
# =============================================================================

@router.post("/items/{item_id}/move")
async def move_item(
    item_id: uuid.UUID,
    body: MoveItemRequest,
    request: Request,
    token_payload: dict = Depends(require_section_permission(PermissionLevelEnum.WRITE)),
    db: AsyncSession = Depends(get_db),
):
    item = await WarehouseService(db).move_item(
        item_id, body, uuid.UUID(token_payload["sub"]), _ip(request)
    )
    return success_response(data=_item_out(item))


# =============================================================================
# MOVEMENT HISTORY (Feature 5)
# =============================================================================

@router.get("/items/{item_id}/history")
async def item_history(
    item_id: uuid.UUID,
    request: Request,
    token_payload: dict = Depends(require_section_permission(PermissionLevelEnum.READ)),
    db: AsyncSession = Depends(get_db),
):
    logs = await WarehouseService(db).get_history(
        item_id, uuid.UUID(token_payload["sub"]), _ip(request)
    )
    return success_response(data=[_movement_history_out(m) for m in logs])
