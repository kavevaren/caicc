"""Auth dependency and the in-memory rate limiter (SPEC §6).

Bearer token in Authorization: the Studio embeds the app in a cross-site
iframe where cookies are unreliable, so the token lives in localStorage.
"""
from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import Header

from server.api.errors import APIError
from server.store import db

# Rate limits per user per minute (SPEC §6).
AI_LIMIT_PER_MIN = 20
UPLOAD_LIMIT_PER_MIN = 10


def get_current_user(authorization: str = Header(default="")) -> dict[str, Any]:
    """Resolve the Bearer token to the current user row."""
    token = authorization[7:] if authorization.startswith("Bearer ") else None
    if not token:
        raise APIError("unauthenticated", 401)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    row = db.read_one(
        "SELECT u.id, u.username, u.display_name, u.lang, u.theme, u.reduce_motion,"
        " u.onboarding_done FROM sessions s JOIN users u ON u.id = s.user_id"
        " WHERE s.token_hash = ? AND s.expires_at > datetime('now')",
        (token_hash,),
    )
    if row is None:
        raise APIError("unauthenticated", 401)
    return dict(row)


class RateLimiter:
    """In-memory sliding window: {key: deque of timestamps} (process-wide)."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit_per_min: int) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > 60.0:
                q.popleft()
            if len(q) >= limit_per_min:
                return False
            q.append(now)
            return True


_ai_limiter = RateLimiter()
_upload_limiter = RateLimiter()


def require_ai_rate(user: dict[str, Any]) -> None:
    if not _ai_limiter.allow(f"ai:{user['id']}", AI_LIMIT_PER_MIN):
        raise APIError("rate_limited", 429)


def require_upload_rate(user: dict[str, Any]) -> None:
    if not _upload_limiter.allow(f"upload:{user['id']}", UPLOAD_LIMIT_PER_MIN):
        raise APIError("rate_limited", 429)
