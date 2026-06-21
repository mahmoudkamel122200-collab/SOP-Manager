"""
utils/token_blacklist.py

In-memory JWT token revocation store.

How it works:
  - On logout, the token's `jti` (JWT ID) is added to the blacklist set.
  - `decode_access_token` checks the blacklist before accepting a token.
  - Entries expire automatically via a TTL dict so memory doesn't grow forever.

MVP trade-off:
  - In-memory → cleared on server restart (acceptable for demo).
  - Production upgrade → swap with Redis SETEX(jti, ttl_seconds, "1").

Thread safety:
  - asyncio is single-threaded per event loop, so a plain set/dict is safe.
  - For multi-process deployments (gunicorn workers) you MUST use Redis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


class TokenBlacklist:
    """Simple TTL-aware in-memory token blacklist."""

    def __init__(self) -> None:
        # {jti: expires_at (UTC datetime)}
        self._store: dict[str, datetime] = {}

    def add(self, jti: str, expires_at: datetime) -> None:
        """Blacklist a token by its JTI until its natural expiry."""
        self._purge_expired()
        self._store[jti] = expires_at

    def is_blacklisted(self, jti: str) -> bool:
        """Return True if the JTI is in the blacklist and hasn't expired yet."""
        expiry = self._store.get(jti)
        if expiry is None:
            return False
        if datetime.now(timezone.utc) > expiry:
            # Token has naturally expired — remove from store
            del self._store[jti]
            return False
        return True

    def _purge_expired(self) -> None:
        """Clean up entries that have already passed their natural expiry."""
        now = datetime.now(timezone.utc)
        expired = [jti for jti, exp in self._store.items() if now > exp]
        for jti in expired:
            del self._store[jti]

    @property
    def size(self) -> int:
        """Number of active blacklisted tokens (useful for monitoring)."""
        self._purge_expired()
        return len(self._store)


# ── Singleton ─────────────────────────────────────────────────────────────────
# One shared instance for the entire process lifetime.
# Import this anywhere: from app.utils.token_blacklist import blacklist
blacklist = TokenBlacklist()
