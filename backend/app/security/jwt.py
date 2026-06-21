"""
Security utilities: JWT creation/decoding + Argon2 password hashing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

# ── Argon2 hasher ─────────────────────────────────────────────────────────────
_ph = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)

bearer_scheme = HTTPBearer(auto_error=True)


# ── Password Hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plain-text password with Argon2id."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain-text password against an Argon2 hash.
    Returns True on match, False on mismatch.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Return True if the hash should be re-hashed (param changes)."""
    return _ph.check_needs_rehash(hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def _make_token(
    subject: str,
    extra_claims: dict,
    secret: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),   # unique token ID — needed for revocation
        **extra_claims,
    }
    return jwt.encode(payload, secret, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str, role: str, section_id: Optional[str] = None) -> str:
    """
    Create a short-lived access token.
    Optional `section_id` is embedded when an employee selects a section.
    """
    claims: dict = {"role": role, "type": "access"}
    if section_id:
        claims["section_id"] = section_id
    return _make_token(
        subject=user_id,
        extra_claims=claims,
        secret=settings.SECRET_KEY,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token (stored in HttpOnly cookie ideally)."""
    return _make_token(
        subject=user_id,
        extra_claims={"type": "refresh"},
        secret=settings.REFRESH_SECRET_KEY,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token."""
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


# ── FastAPI Dependencies ───────────────────────────────────────────────────────

def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Dependency: decode the bearer token and return its payload."""
    return decode_access_token(credentials.credentials)


def require_role(*roles: str):
    """
    Dependency factory: ensures the authenticated user has one of the given roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("ADMIN"))])
    """
    def _checker(token_payload: dict = Depends(get_current_token)) -> dict:
        if token_payload.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )
        return token_payload
    return _checker
