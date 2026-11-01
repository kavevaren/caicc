"""Orvina AI package (SPEC §7).

Only this package may import `openai` (SPEC §2.1); only llm.py (P2) creates
a client. P1: the SPEC §7 function signatures (NotImplementedError), the P0
platform probe (probe.py), and FakeLLM for tests.
"""
from __future__ import annotations

from typing import Any, Callable

from server.ai.probe import modelscope_probe, ms_state, trigger_whisper_load, whisper_state


class AIError(Exception):
    """AI pipeline failure with a translated code (SPEC §7)."""

    def __init__(self, code: str, params: dict | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.params = params or {}


def health() -> dict[str, Any]:
    """SPEC §7: {modelscope, whisper}. Uses the cached probe (no live call)."""
    return {"modelscope": ms_state()["status"], "whisper": whisper_state()["status"]}


def summarize(job_id: str, files: list[dict], options: dict, on_stage: Callable[[str], None]) -> dict[str, Any]:
    """SPEC §7 F1: files [{path, name, mime}], options {style, lang, detail, extra, include_figures, generate_charts}."""
    raise NotImplementedError("P2: ai/summarize.py")


def transcribe(job_id: str, path: str, options: dict, on_stage: Callable[[str], None]) -> dict[str, Any]:
    """SPEC §7 F2: media or transcript file; options {source_lang, targets[], summary}."""
    raise NotImplementedError("P2: ai/transcribe.py")


def forum_similar(title: str, body: str, candidates: list[dict]) -> dict[str, Any]:
    """SPEC §7: candidates = FTS5 top 10 [{id, title, excerpt}] -> {ids[<=3]}."""
    raise NotImplementedError("P2: ai/forum_ai.py")


def forum_tags(title: str, body: str) -> dict[str, Any]:
    """SPEC §7: -> {tags[<=5]} lowercase."""
    raise NotImplementedError("P2: ai/forum_ai.py")


def forum_moderate(text: str) -> dict[str, Any]:
    """SPEC §7: -> {allowed, reason_key}; fails open on API error."""
    raise NotImplementedError("P2: ai/forum_ai.py")


def forum_hint(question_md: str, answers_md: str, lang: str) -> dict[str, Any]:
    """SPEC §7: -> {hint_md}; a hint or guiding question, never the final answer."""
    raise NotImplementedError("P2: ai/forum_ai.py")


class FakeLLM:
    """Deterministic stand-in for the ModelScope client, for tests (P1+).

    Returns canned results per role/feature so pipelines and routers can be
    tested without network access. P2 routes the real client through the
    same shape: chat(role, messages, *, json_schema=None, feature="...").
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def chat(self, role: str, messages: list[dict], *, json_schema: dict | None = None, feature: str = "test") -> dict[str, Any]:
        self.calls.append({"role": role, "feature": feature, "messages": messages, "json_schema": json_schema})
        if feature == "summarize":
            return {"content_md": "# Ringkasan palsu\n\nIsi untuk uji.", "figures": [], "sources": [], "deadlines": []}
        if feature == "transcribe":
            return {"language": "id", "segments": [], "translations": {}, "meeting": {"summary_md": "", "decisions": [], "action_items": []}}
        if feature == "forum_similar":
            return {"ids": []}
        if feature == "forum_tags":
            return {"tags": ["uji"]}
        if feature == "forum_moderate":
            return {"allowed": True, "reason_key": "ok"}
        if feature == "forum_hint":
            return {"hint_md": "Coba uraikan langkah pertama terlebih dahulu."}
        return {"ok": True}


__all__ = [
    "AIError",
    "FakeLLM",
    "health",
    "summarize",
    "transcribe",
    "forum_similar",
    "forum_tags",
    "forum_moderate",
    "forum_hint",
    "modelscope_probe",
    "ms_state",
    "trigger_whisper_load",
    "whisper_state",
]
