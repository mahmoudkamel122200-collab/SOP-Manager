"""
Warehouse ORM Models
Tables: locations, items, movement_logs
Module: Warehouse Management
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ItemStatusEnum(str, enum.Enum):
    AVAILABLE  = "AVAILABLE"
    RESERVED   = "RESERVED"
    CONSUMED   = "CONSUMED"
    DAMAGED    = "DAMAGED"
    QUARANTINE = "QUARANTINE"


class Location(Base):
    """
    Physical warehouse storage position.
    Identified by a composite code: WAREHOUSE-RACK-SHELF-POSITION
    Example: A-R01-S03-P05
    """

    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    warehouse_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rack: Mapped[str] = mapped_column(String(20), nullable=False)
    shelf: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[str] = mapped_column(String(20), nullable=False)
    location_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    items: Mapped[list["Item"]] = relationship("Item", back_populates="location")
    movements_from: Mapped[list["MovementLog"]] = relationship(
        "MovementLog",
        foreign_keys="MovementLog.from_location",
        back_populates="from_loc",
    )
    movements_to: Mapped[list["MovementLog"]] = relationship(
        "MovementLog",
        foreign_keys="MovementLog.to_location",
        back_populates="to_loc",
    )

    __table_args__ = (
        Index("idx_locations_warehouse_name", "warehouse_name"),
        Index("idx_locations_location_code",  "location_code"),
        CheckConstraint(
            "location_code ~ '^[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+$'",
            name="chk_locations_code_format",
        ),
    )

    def __repr__(self) -> str:
        return f"<Location code={self.location_code!r}>"


class Item(Base):
    """
    Warehouse item — a material or bag tracked by a barcode-style code.
    Example code: BG-000123 (prefix + 6-digit number)
    """

    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    material_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ItemStatusEnum] = mapped_column(
        Enum(ItemStatusEnum, name="item_status_enum"),
        nullable=False,
        default=ItemStatusEnum.AVAILABLE,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    location: Mapped["Location"] = relationship("Location", back_populates="items")
    creator: Mapped["User"] = relationship("User", back_populates="items_created")  # type: ignore[name-defined]
    movement_logs: Mapped[list["MovementLog"]] = relationship(
        "MovementLog", back_populates="item"
    )

    __table_args__ = (
        Index("idx_items_item_code",   "item_code"),
        Index("idx_items_location_id", "location_id"),
        Index("idx_items_status",      "status"),
        Index("idx_items_created_by",  "created_by"),
        CheckConstraint("quantity >= 0", name="chk_items_quantity_non_negative"),
        CheckConstraint(
            "item_code ~ '^[A-Z]{2}-\\d{6}$'",
            name="chk_items_code_format",
        ),
    )

    def __repr__(self) -> str:
        return f"<Item code={self.item_code!r} qty={self.quantity} {self.unit}>"


class MovementLog(Base):
    """
    Immutable ledger of every warehouse item movement.
    from_location is NULL on initial item placement.
    """

    __tablename__ = "movement_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    from_location: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    to_location: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    moved_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    item: Mapped["Item"] = relationship("Item", back_populates="movement_logs")
    from_loc: Mapped[Optional["Location"]] = relationship(
        "Location",
        foreign_keys=[from_location],
        back_populates="movements_from",
    )
    to_loc: Mapped["Location"] = relationship(
        "Location",
        foreign_keys=[to_location],
        back_populates="movements_to",
    )
    mover: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        foreign_keys=[moved_by],
        back_populates="movements",
    )

    __table_args__ = (
        Index("idx_movement_logs_item_id",      "item_id"),
        Index("idx_movement_logs_to_location",  "to_location"),
        Index("idx_movement_logs_moved_by",     "moved_by"),
        Index("idx_movement_logs_created_at",   "created_at"),
        CheckConstraint(
            "from_location IS NULL OR from_location <> to_location",
            name="chk_movement_logs_different_locations",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MovementLog item={self.item_id} "
            f"from={self.from_location} to={self.to_location}>"
        )
