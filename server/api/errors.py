"""Error JSON and global exception handlers (SPEC §6).

User-facing errors are translated JSON:
    {"error": {"code": "...", "message_key": "errors.<code>"}}
A stack trace must never reach the browser; details go to the log.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

log = logging.getLogger("orvina.api")


class APIError(Exception):
    """Raise from routers; the handler turns it into the error JSON."""

    def __init__(self, code: str, status: int = 400, params: dict | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.params = params or {}


def error_response(code: str, status: int) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message_key": f"errors.{code}"}},
        status_code=status,
    )


def not_implemented() -> JSONResponse:
    """P1 skeleton stub response (implemented in later phases)."""
    return error_response("not_implemented", 501)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def _api_error(request: Request, exc: APIError) -> JSONResponse:
        return error_response(exc.code, exc.status)

    @app.exception_handler(HTTPException)
    async def _http_error(request: Request, exc: HTTPException) -> JSONResponse:
        code = {401: "unauthenticated", 404: "not_found"}.get(exc.status_code)
        if code is None:
            code = "internal_error" if exc.status_code >= 500 else "not_found"
        return error_response(code, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        log.info("validation error on %s %s: %s", request.method, request.url.path, exc.errors()[:5])
        return error_response("validation", 422)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return error_response("internal_error", 500)
