"""Files router (SPEC §6): attachment download. P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Files"])


@router.get("/api/files/{attachment_id}")
def get_file(attachment_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
