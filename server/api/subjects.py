"""Subjects router (SPEC §6). P1 skeleton: 501 not_implemented until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Subjects"])


class CreateSubjectRequest(BaseModel):
    name: str


@router.get("/api/subjects")
def list_subjects(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/subjects")
def create_subject(body: CreateSubjectRequest, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
