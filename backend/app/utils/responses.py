"""
Standardised JSON response helpers — enforces the API envelope.
"""

from typing import Any

from fastapi.responses import JSONResponse


def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """
    { "status": "success", "data": ... }
    """
    return JSONResponse(
        status_code=status_code,
        content={"status": "success", "data": data},
    )


def paginated_response(
    data: list,
    total: int,
    page: int,
    page_size: int,
) -> JSONResponse:
    """
    { "status": "success", "data": [...], "total": N, "page": N, "page_size": N }
    """
    return JSONResponse(
        content={
            "status": "success",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


def error_response(message: str, code: str, status_code: int = 400) -> JSONResponse:
    """
    { "status": "error", "message": "...", "code": "..." }
    """
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message, "code": code},
    )
