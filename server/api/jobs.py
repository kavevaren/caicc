"""Jobs router (SPEC §6): job state + SSE stream. P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Jobs"])


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/jobs/{job_id}/stream")
def stream_job(job_id: str, ticket: str = Query(min_length=1), user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
