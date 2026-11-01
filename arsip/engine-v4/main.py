"""Orvina AI engine — P0 hello stack.

FastAPI app bound to 127.0.0.1:8001, internal only. Every request must carry
the X-Engine-Key header (HMAC-SHA256 of APP_SECRET_KEY over "engine").

/v1/health does one tiny FAST call to ModelScope and loads whisper `tiny`
once in the background, reporting ok / invalid_token / unreachable and
ready / loading / disabled.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException

MODELSCOPE_BASE = "https://api-inference.modelscope.ai/v1"
FAST_MODEL = "stepfun-ai/Step-3.5-Flash"
ALLOWED_MODELS = {
    "zai-org/GLM-5.2",
    "deepseek-ai/DeepSeek-V4-Pro-0813",
    "stepfun-ai/Step-3.5-Flash",
    "Qwen/Qwen3.8-27B",
}
VERSION = "0.1.0-p0"

app = FastAPI(title="Orvina engine", version=VERSION)

# --- state -----------------------------------------------------------------
_engine_key: str | None = None
_token: str | None = os.environ.get("MODELSCOPE_TOKEN") or None
_whisper_state: dict[str, Any] = {"status": "disabled", "lock": threading.Lock()}
if os.environ.get("ENABLE_TRANSCRIPTION", "true").lower() != "false":
    _whisper_state["status"] = "loading"


def set_engine_key() -> None:
    global _engine_key
    _engine_key = os.environ.get("X_ENGINE_KEY")


set_engine_key()


def require_engine_key(x_engine_key: str = Header(default="")) -> None:
    if not _engine_key or x_engine_key != _engine_key:
        raise HTTPException(status_code=401, detail="bad engine key")


# --- modelscope health -------------------------------------------------------
def modelscope_probe() -> tuple[str, int]:
    """One tiny FAST chat completion. Returns (status, latency_ms)."""
    if not _token:
        return "invalid_token", 0
    try:
        from openai import OpenAI

        client = OpenAI(base_url=f"{MODELSCOPE_BASE}", api_key=_token, timeout=30.0)
        t0 = time.monotonic()
        resp = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        assert resp is not None
        return "ok", int((time.monotonic() - t0) * 1000)
    except Exception as exc:  # noqa: BLE001 - mapped below
        msg = str(exc).lower()
        if "401" in msg or "unauthorized" in msg:
            return "invalid_token", 0
        return "unreachable", 0


# --- whisper loader ----------------------------------------------------------
def _load_whisper() -> None:
    name = os.environ.get("LIVE_WHISPER_MODEL", "tiny")
    data_dir = os.environ.get("DATA_DIR", "/tmp/orvina")
    local_dir = os.path.join(data_dir, "models")
    os.makedirs(local_dir, exist_ok=True)
    with _whisper_state["lock"]:
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel(name, device="cpu", compute_type="int8", download_root=local_dir)
            _whisper_state["model"] = model
            _whisper_state["status"] = "ready"
        except Exception as exc:  # noqa: BLE001
            _whisper_state["status"] = f"error: {exc}"[:120]


threading.Thread(target=_load_whisper, daemon=True).start()


# --- routes ------------------------------------------------------------------
@app.get("/v1/health", dependencies=[Depends(require_engine_key)])
def health() -> dict[str, Any]:
    ms_status, ms_ms = modelscope_probe()
    return {
        "modelscope": ms_status,
        "modelscope_latency_ms": ms_ms,
        "whisper": _whisper_state["status"],
        "version": VERSION,
    }


@app.on_event("startup")
def _startup() -> None:
    # Re-read env in case uvicorn spawned us differently.
    set_engine_key()
