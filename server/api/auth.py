"""Auth router (SPEC §6). P1 skeleton: 501 not_implemented until P3."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from server.api.errors import not_implemented

router = APIRouter(tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str
    display_name: str
    password: str
    lang: str = "id"
    accept_terms: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


class StreamTicketRequest(BaseModel):
    job_id: str


@router.post("/api/auth/register")
def register(body: RegisterRequest) -> object:
    return not_implemented()


@router.post("/api/auth/login")
def login(body: LoginRequest) -> object:
    return not_implemented()


@router.post("/api/auth/logout")
def logout() -> object:
    return not_implemented()


@router.post("/api/stream-ticket")
def create_stream_ticket(body: StreamTicketRequest) -> object:
    return not_implemented()
