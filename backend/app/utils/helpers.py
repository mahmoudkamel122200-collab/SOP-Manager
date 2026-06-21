"""
utils/helpers.py

General-purpose utility functions used across the application.
"""

from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extract the real client IP, respecting X-Forwarded-For (reverse proxy).
    Returns 'unknown' if no IP is determinable.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def build_location_code(warehouse: str, rack: str, shelf: str, position: str) -> str:
    """
    Generate a standardised warehouse location code.
    Example: ('A', 'R01', 'S03', 'P05') → 'A-R01-S03-P05'
    """
    parts = [warehouse.strip(), rack.strip(), shelf.strip(), position.strip()]
    code  = "-".join(p.upper() for p in parts)
    return code


def paginate(query_result: list, page: int, page_size: int) -> tuple[list, int]:
    """
    In-memory pagination helper (use only for small lists; prefer DB-level pagination).
    Returns (page_items, total).
    """
    total = len(query_result)
    start = (page - 1) * page_size
    end   = start + page_size
    return query_result[start:end], total
