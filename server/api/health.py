"""Health router (SPEC §6): server / modelscope (cached) / whisper / version."""
from __future__ import annotations

from fastapi import APIRouter

from server import __version__
from server.ai import health as ai_health
from server.ai.probe import ms_state

router = APIRouter(tags=["Health"])


@router.get("/api/health")
def health() -> dict:
    h = ai_health()
    return {
        "server": "ok",
        "modelscope": h["modelscope"],
        "modelscope_latency_ms": ms_state()["latency_ms"],
        "whisper": h["whisper"],
        "version": __version__,
    }
