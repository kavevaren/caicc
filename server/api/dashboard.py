"""Dashboard router (SPEC §6, §8.2). P1 skeleton: 501 not_implemented until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Dashboard"])


@router.get("/api/dashboard")
def get_dashboard(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
