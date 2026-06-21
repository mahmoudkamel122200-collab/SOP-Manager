"""
services/warehouse_service.py

Warehouse business logic:
  - list/create locations
  - list / get items
  - create item (with initial movement log)
  - move item (with movement log + audit)
  - item movement history
"""

from __future__ import annotations

import re
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.warehouse import Item, ItemStatusEnum, Location, MovementLog
from app.models.audit_log import AuditActionEnum, AuditModuleEnum
from app.schemas.warehouse import ItemCreateRequest, ItemCreateWithNewLocationRequest, MoveItemRequest, LocationCreateRequest
from app.services.audit_service import log_event


def derive_warehouse_code(name: str) -> str:
    """
    Extract a clean uppercase code from a warehouse name.
    Example: "Warehouse A" -> "A"
             "Warehouse-B" -> "B"
             "A"           -> "A"
    """
    name = name.strip()
    segments = re.split(r'[\s\-]+', name)
    if len(segments) > 1:
        last = segments[-1].upper()
        if re.match(r'^[A-Z0-9]+$', last):
            return last
    clean = re.sub(r'[^A-Z0-9]', '', name.upper())
    return clean if clean else "WH"


class WarehouseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Locations ─────────────────────────────────────────────────────────────
    async def list_locations(self) -> list[Location]:
        result = await self.db.execute(
            select(Location).order_by(
                Location.warehouse_name, Location.rack, Location.shelf, Location.position
            )
        )
        return result.scalars().all()

    async def get_location_or_404(self, location_id: uuid.UUID) -> Location:
        loc = await self.db.get(Location, location_id)
        if not loc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")
        return loc

    async def create_location(
        self, body: LocationCreateRequest, creator_id: uuid.UUID, ip: Optional[str]
    ) -> Location:
        wh_code = derive_warehouse_code(body.warehouse_name)
        location_code = f"{wh_code}-{body.rack.strip().upper()}-{body.shelf.strip().upper()}-{body.position.strip().upper()}"

        # Duplicate location check
        existing = await self.db.execute(
            select(Location).where(Location.location_code == location_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Location code '{location_code}' already exists.",
            )

        location = Location(
            warehouse_name=body.warehouse_name,
            rack=body.rack.strip(),
            shelf=body.shelf.strip(),
            position=body.position.strip(),
            location_code=location_code,
        )
        self.db.add(location)
        await self.db.flush()

        await log_event(
            self.db,
            action=AuditActionEnum.CREATE_LOCATION,
            module=AuditModuleEnum.WAREHOUSE,
            user_id=creator_id,
            target_id=location.id,
            description=f"Created location {location_code} ({body.warehouse_name})",
            ip_address=ip,
        )
        return location

    # ── Items ─────────────────────────────────────────────────────────────────
    async def list_items(
        self,
        page: int,
        page_size: int,
        status_filter: Optional[str],
    ) -> tuple[list[Item], int]:
        q = select(Item).options(selectinload(Item.location))
        if status_filter:
            try:
                q = q.where(Item.status == ItemStatusEnum(status_filter))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}",
                )

        total = (await self.db.execute(select(func.count(Item.id)))).scalar_one()
        items = (
            await self.db.execute(
                q.order_by(Item.created_at.desc())
                 .offset((page - 1) * page_size)
                 .limit(page_size)
            )
        ).scalars().all()
        return items, total

    async def get_by_code(self, item_code: str, user_id: uuid.UUID, ip: Optional[str]) -> Item:
        result = await self.db.execute(
            select(Item)
            .where(Item.item_code == item_code.upper())
            .options(selectinload(Item.location))
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item '{item_code}' not found.",
            )

        await log_event(
            self.db,
            action=AuditActionEnum.SEARCH_ITEM,
            module=AuditModuleEnum.WAREHOUSE,
            user_id=user_id,
            target_id=item.id,
            description=f"Searched item {item.item_code}",
            ip_address=ip,
        )
        return item

    # ── Create Item ───────────────────────────────────────────────────────────
    async def create_item(
        self, body: ItemCreateRequest, creator_id: uuid.UUID, ip: Optional[str]
    ) -> Item:
        # Uniqueness check
        existing = await self.db.execute(
            select(Item).where(Item.item_code == body.item_code.upper())
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Item code '{body.item_code}' already exists.",
            )

        location = await self.get_location_or_404(body.location_id)

        item = Item(
            item_code=body.item_code.upper(),
            material_name=body.material_name,
            quantity=body.quantity,
            unit=body.unit,
            location_id=body.location_id,
            created_by=creator_id,
        )
        self.db.add(item)
        await self.db.flush()   # get item.id

        # Record initial placement
        self.db.add(
            MovementLog(
                item_id=item.id,
                from_location=None,
                to_location=body.location_id,
                moved_by=creator_id,
                notes="Initial item placement.",
            )
        )

        await log_event(
            self.db,
            action=AuditActionEnum.CREATE_ITEM,
            module=AuditModuleEnum.WAREHOUSE,
            user_id=creator_id,
            target_id=item.id,
            description=f"Added {item.item_code} → {location.location_code}",
            ip_address=ip,
        )

        await self.db.refresh(item, ["location"])
        return item

    # ── Create Item with New Location (single transaction) ────────────────────
    async def create_item_with_location(
        self, body: ItemCreateWithNewLocationRequest, creator_id: uuid.UUID, ip: Optional[str]
    ) -> Item:
        # 1) Create the location first (within the same session/transaction)
        loc_body = LocationCreateRequest(
            warehouse_name=body.warehouse_name,
            rack=body.rack,
            shelf=body.shelf,
            position=body.position,
        )
        location = await self.create_location(loc_body, creator_id, ip)

        # 2) Create the item referencing the just-created location
        item_body = ItemCreateRequest(
            item_code=body.item_code,
            material_name=body.material_name,
            quantity=body.quantity,
            unit=body.unit,
            location_id=location.id,
        )
        return await self.create_item(item_body, creator_id, ip)

    # ── Move Item ─────────────────────────────────────────────────────────────
    async def move_item(
        self,
        item_id: uuid.UUID,
        body: MoveItemRequest,
        mover_id: uuid.UUID,
        ip: Optional[str],
    ) -> Item:
        result = await self.db.execute(
            select(Item).where(Item.id == item_id).options(selectinload(Item.location))
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

        # Accept body.to_location_id via MoveItemRequest (which gets mapped to new_location_id)
        # Note: MoveItemRequest has Field(..., serialization_alias="new_location_id")
        target_location_id = body.to_location_id

        if item.location_id == target_location_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item is already at this location.",
            )

        to_location = await self.get_location_or_404(target_location_id)

        old_location_id = item.location_id
        from_code       = item.location.location_code if item.location else "?"

        # Log movement
        self.db.add(
            MovementLog(
                item_id=item.id,
                from_location=old_location_id,
                to_location=target_location_id,
                moved_by=mover_id,
                notes=body.notes,
            )
        )

        # Update item position
        item.location_id = target_location_id

        await log_event(
            self.db,
            action=AuditActionEnum.MOVE_ITEM,
            module=AuditModuleEnum.WAREHOUSE,
            user_id=mover_id,
            target_id=item.id,
            description=f"Moved {item.item_code}: {from_code} → {to_location.location_code}",
            ip_address=ip,
        )

        await self.db.refresh(item, ["location"])
        return item

    # ── History ───────────────────────────────────────────────────────────────
    async def get_history(self, item_id: uuid.UUID, user_id: uuid.UUID, ip: Optional[str]) -> list[MovementLog]:
        # First verify the item exists
        item = await self.db.get(Item, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found.",
            )

        result = await self.db.execute(
            select(MovementLog)
            .where(MovementLog.item_id == item_id)
            .options(
                selectinload(MovementLog.from_loc),
                selectinload(MovementLog.to_loc),
                selectinload(MovementLog.mover),
            )
            .order_by(MovementLog.created_at.desc())
        )
        logs = result.scalars().all()

        await log_event(
            self.db,
            action=AuditActionEnum.VIEW_HISTORY,
            module=AuditModuleEnum.WAREHOUSE,
            user_id=user_id,
            target_id=item_id,
            description=f"Viewed movement history for item {item.item_code}",
            ip_address=ip,
        )
        return logs
