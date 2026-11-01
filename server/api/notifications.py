"""Notifications router (SPEC §6). P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Notifications"])


@router.get("/api/notifications")
def list_notifications(unread: int = Query(default=0, ge=0, le=1), user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/notifications/read-all")
def mark_all_read(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/notifications/{notification_id}/read")
def mark_read(notification_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
