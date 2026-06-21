"""
Role ORM Model
Table: roles
Module: Identity & Access Management
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="role")  # type: ignore[name-defined]

    __table_args__ = (
        CheckConstraint("TRIM(name) <> ''", name="chk_roles_name_not_empty"),
    )

    def __repr__(self) -> str:
        return f"<Role name={self.name!r}>"
