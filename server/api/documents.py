"""F1 router (SPEC §6): summaries, documents, figures. P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, UploadFile

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Summaries (F1)"])


@router.post("/api/summaries")
def create_summary(
    files: list[UploadFile],
    title: str | None = Form(default=None),
    subject_id: int | None = Form(default=None),
    style: str = Form(default="structured_notes"),
    lang: str = Form(default="id"),
    detail: str = Form(default="standar"),
    extra: str | None = Form(default=None),
    include_figures: bool = Form(default=True),
    generate_charts: bool = Form(default=True),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()


@router.get("/api/documents")
def list_documents(
    kind: str | None = Query(default=None),
    q: str | None = Query(default=None),
    subject: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()


@router.get("/api/documents/{document_id}")
def get_document(document_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.patch("/api/documents/{document_id}")
def patch_document(document_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.delete("/api/documents/{document_id}")
def delete_document(document_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.patch("/api/documents/{document_id}/figures/{ref}")
def patch_figure(document_id: int, ref: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/documents/{document_id}/export")
def export_document(document_id: int, format: str = Query(pattern="^(md|html)$"), user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/figures/{figure_id}.png")
def get_figure_png(figure_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
