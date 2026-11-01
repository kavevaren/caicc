"""F2 router (SPEC §6): transcripts. P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, UploadFile

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Transcripts (F2)"])


@router.post("/api/transcripts")
def create_transcript(
    file: UploadFile,
    title: str | None = Form(default=None),
    source_lang: str = Form(default="auto"),
    targets: str = Form(default=""),
    summary: bool = Form(default=True),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()
