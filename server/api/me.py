"""Me router (SPEC §6). P1 skeleton: 501 not_implemented until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Me"])


class PatchMeRequest(BaseModel):
    display_name: str | None = None
    lang: str | None = None
    theme: str | None = None
    reduce_motion: bool | None = None
    notif_prefs: dict | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class OnboardingRequest(BaseModel):
    lang: str
    subject_ids: list[int]
    new_subjects: list[str]
    done: bool


@router.get("/api/me")
def get_me(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.patch("/api/me")
def patch_me(body: PatchMeRequest, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/me/password")
def change_password(body: ChangePasswordRequest, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/me/onboarding")
def complete_onboarding(body: OnboardingRequest, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
