"""
Shared SQLAlchemy declarative base.
Import this in every model file — never create a second Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Root declarative base for all ORM models."""
    pass
