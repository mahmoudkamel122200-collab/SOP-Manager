"""
core/security.py

The complete cryptographic + authentication dependency layer.

Responsibilities:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  PASSWORD       Argon2id hash / verify / rehash-check               │
  │  JWT            create_access_token / create_refresh_token           │
  │                 decode_access_token / decode_refresh_token           │
  │  BLACKLIST      integration with token_blacklist for logout support  │
  │  DEPENDENCIES   get_current_token  → raw JWT payload dict            │
  │                 get_current_user   → full User ORM object            │
  │                 require_role()     → role-gated dependency factory   │
  └─────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings

# ── Lazy imports to avoid circular deps ──────────────────────────────────────
# These are imported inside functions / at the bottom to prevent import cycles.


# =============================================================================
# PASSWORD HASHING  (Argon2id)
# =============================================================================

_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)

bearer_scheme = HTTPBearer(auto_error=True)


def hash_password(plain: str) -> str:
    """
    Hash a plain-text password with Argon2id.

    Argon2id parameters (from .env):
      - time_cost:    CPU iterations (default 2)
      - memory_cost:  KB of RAM used (default 65536 = 64 MB)
      - parallelism:  parallel threads (default 2)

    NEVER store or log plain-text passwords.
    """
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain-text password against an Argon2 hash.
    Returns True on match, False on any mismatch or malformed hash.
    Constant-time comparison — safe against timing attacks.
    """
    try:
        return _hasher.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """
    True if the stored hash was created with outdated Argon2 parameters.
    Call this after a successful login and re-hash if True.
    """
    return _hasher.check_needs_rehash(hashed)


# =============================================================================
# JWT TOKEN CREATION
# =============================================================================

def _build_token(
    subject: str,
    extra_claims: dict,
    secret: str,
    expires_delta: timedelta,
) -> str:
    """
    Internal: sign a JWT with standard + custom claims.

    Standard claims:
      sub  — subject (user UUID as string)
      iat  — issued at
      exp  — expiration
      jti  — unique token ID (used for blacklist / revocation)
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
        **extra_claims,
    }
    return jwt.encode(payload, secret, algorithm=settings.ALGORITHM)


def create_access_token(
    user_id: str,
    role: str,
    section_id: Optional[str] = None,
) -> str:
    """
    Create a short-lived access token (default: 30 min).

    Claims embedded:
      type        → "access"
      role        → "ADMIN" | "EMPLOYEE"
      section_id  → UUID string (present only after /auth/select-section)

    The section_id claim is what enables section-scoped authorization
    without an extra DB query on every request.
    """
    claims: dict = {"type": "access", "role": role}
    if section_id:
        claims["section_id"] = section_id
    return _build_token(
        subject=user_id,
        extra_claims=claims,
        secret=settings.SECRET_KEY,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived refresh token (default: 7 days).

    Stored only in the client; never cached server-side.
    Uses a SEPARATE secret so a leaked access secret doesn't
    compromise refresh tokens.
    """
    return _build_token(
        subject=user_id,
        extra_claims={"type": "refresh"},
        secret=settings.REFRESH_SECRET_KEY,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# =============================================================================
# JWT TOKEN DECODING
# =============================================================================

def decode_access_token(token: str) -> dict:
    """
    Decode + validate an access token.

    Checks performed (in order):
      1. Signature validity (HS256 with SECRET_KEY)
      2. Expiration (exp claim)
      3. Token type must be "access"
      4. JTI not on the blacklist (logout support)

    Raises HTTP 401 on any failure.
    """
    from app.utils.token_blacklist import blacklist   # avoid circular import

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    # Blacklist check (logout support)
    jti = payload.get("jti")
    if jti and blacklist.is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
        )

    return payload


def decode_refresh_token(token: str) -> dict:
    """
    Decode + validate a refresh token.
    Uses the REFRESH_SECRET_KEY — separate from access tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.REFRESH_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    return payload


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Dependency — Level 1: Parse + decode the bearer token.
    Returns the raw JWT payload dict.

    Use this when you only need claims (user_id, role, section_id)
    without loading the User from the database.
    """
    return decode_access_token(credentials.credentials)


async def get_current_user(
    token_payload: dict = Depends(get_current_token),
    db: AsyncSession = Depends(None),   # overridden below — see note
):
    """
    Dependency — Level 2: Load the full User ORM object.

    Also checks:
      - User exists in the database
      - User is_active (blocks soft-deleted / banned accounts)
      - Optionally re-hashes password if Argon2 params changed

    Usage:
        @router.get("/profile")
        async def profile(user: User = Depends(get_current_user)):
            return user.username
    """
    from app.models.user import User  # local import to avoid circular deps
    from app.core.database import get_db

    # This dependency needs the DB — inject it properly below
    raise NotImplementedError("Use get_current_user_dep instead")


# ── Proper version with DB injection ─────────────────────────────────────────
def _make_get_current_user():
    """
    Factory that produces the real get_current_user dependency with proper
    DB session injection. Called once at import time.
    """
    from app.core.database import get_db
    from app.models.user import User

    async def _get_current_user(
        token_payload: dict = Depends(get_current_token),
        db: AsyncSession = Depends(get_db),
    ) -> "User":
        user_id = uuid.UUID(token_payload["sub"])
        result  = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role))
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled. Contact your administrator.",
            )

        # Transparent hash upgrade (if Argon2 params changed in config)
        # NOTE: We can't re-hash here without the plain password, but we can
        # flag it. In production, re-hash on the next successful login.

        return user

    return _get_current_user


get_current_user = _make_get_current_user()


def require_role(*roles: str):
    """
    Dependency factory — gate an endpoint to one or more roles.

    Checks role from JWT claim (no DB query needed).

    Usage:
        # Single role
        @router.post("/admin-only", dependencies=[Depends(require_role("ADMIN"))])

        # Multiple (OR logic)
        @router.get("/staff", dependencies=[Depends(require_role("ADMIN", "MANAGER"))])

        # Also get the payload
        @router.get("/data")
        async def data(payload: dict = Depends(require_role("ADMIN"))):
            user_id = payload["sub"]
    """
    def _checker(payload: dict = Depends(get_current_token)) -> dict:
        if payload.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}.",
            )
        return payload
    return _checker
