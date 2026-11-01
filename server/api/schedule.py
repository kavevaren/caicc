"""F3 router (SPEC §6): events, suggestions, Google. P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Schedule (F3)"])


@router.get("/api/events")
def list_events(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()


@router.post("/api/events")
def create_event(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.patch("/api/events/{event_id}")
def patch_event(event_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.delete("/api/events/{event_id}")
def delete_event(event_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/events/{event_id}.ics")
def event_ics(event_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/suggestions")
def list_suggestions(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/suggestions/{suggestion_id}/accept")
def accept_suggestion(suggestion_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/suggestions/{suggestion_id}/dismiss")
def dismiss_suggestion(suggestion_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/google/connect")
def google_connect(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/google/callback")
def google_callback(code: str = Query(min_length=1), state: str = Query(min_length=1)) -> object:
    return not_implemented()


@router.delete("/api/google")
def google_disconnect(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
