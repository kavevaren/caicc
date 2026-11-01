"""P0 platform probes — kept until the P0 deploy report is complete.

These endpoints are NOT part of contracts/openapi.yaml; they exist so the
deployed P0 web page can still measure the Studio proxy (SSE buffering,
upload limit, whisper RAM). Remove this module in P2.
"""
from __future__ import annotations

import asyncio
import json
import os
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from server.ai import trigger_whisper_load, whisper_state

router = APIRouter(tags=["P0 probes"])

MAX_PROBE_BYTES = 1 << 30  # 1 GiB hard cap so a runaway upload cannot eat RAM


@router.post("/api/probe/upload")
async def probe_upload(request: Request) -> object:
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_PROBE_BYTES:
            return JSONResponse({"error": {"code": "probe_too_big"}}, status_code=413)
    declared = request.headers.get("content-length")
    return {"received_bytes": total, "declared_bytes": int(declared) if declared else None}


@router.get("/api/probe/sse")
async def probe_sse() -> StreamingResponse:
    async def gen():
        for i in range(1, 21):
            yield f"event: tick\ndata: {json.dumps({'n': i, 't': int(time.time() * 1000)})}\n\n"
            await asyncio.sleep(1.0)
        yield "event: done\ndata: " + json.dumps({"n": 20}) + "\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/probe/whisper")
def probe_whisper() -> dict:
    trigger_whisper_load()
    st = whisper_state()
    out: dict = {"whisper": st["status"]}
    if st["status"] == "disabled":
        out["detail"] = "ENABLE_TRANSCRIPTION=false"
    if st.get("error"):
        out["error"] = st["error"]
    return out


@router.get("/api/probe/config")
def probe_config() -> dict:
    return {"public_app_url": os.environ.get("PUBLIC_APP_URL") or ""}
