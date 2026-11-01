"""Points router (SPEC §6): leaderboard. P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Points"])


@router.get("/api/leaderboard")
def get_leaderboard(
    window: str = Query(default="week", pattern="^(week|month|all)$"),
    subject: int | None = Query(default=None),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()
