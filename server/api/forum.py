"""F4 router (SPEC §6): forum. P1 skeleton: 501 until P3."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, UploadFile

from server.api.deps import get_current_user
from server.api.errors import not_implemented

router = APIRouter(tags=["Forum (F4)"])


@router.get("/api/questions")
def list_questions(
    q: str | None = Query(default=None),
    status: str = Query(default="all"),
    sort: str = Query(default="newest"),
    subject: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()


@router.post("/api/questions")
def create_question(
    title: str = Form(min_length=10, max_length=150),
    body_md: str = Form(max_length=10000),
    subject_id: int = Form(),
    tags: str = Form(default=""),
    files: list[UploadFile] | None = Form(default=None),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()


@router.post("/api/questions/similar")
def similar_questions(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/questions/tags")
def suggest_tags(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.get("/api/questions/{question_id}")
def get_question(question_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.patch("/api/questions/{question_id}")
def patch_question(question_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.delete("/api/questions/{question_id}")
def delete_question(question_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/questions/{question_id}/answers")
def create_answer(
    question_id: int,
    body_md: str = Form(max_length=10000),
    files: list[UploadFile] | None = Form(default=None),
    user: dict = Depends(get_current_user),
) -> object:
    return not_implemented()


@router.post("/api/questions/{question_id}/best")
def mark_best_answer(question_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/questions/{question_id}/follow")
def follow_question(question_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/questions/{question_id}/hint")
def request_hint(question_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.patch("/api/answers/{answer_id}")
def patch_answer(answer_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.delete("/api/answers/{answer_id}")
def delete_answer(answer_id: int, user: dict = Depends(get_current_user)) -> object:
    return not_implemented()


@router.post("/api/votes")
def vote(user: dict = Depends(get_current_user)) -> object:
    return not_implemented()
