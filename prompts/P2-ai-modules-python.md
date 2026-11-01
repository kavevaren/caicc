# P2 · AI modules in Python (Sun 1 Nov) · lane A, can run in parallel with P3 and P4

**Read:** `_RULES.md`, SPEC §2, §3.2 (AI isolation), §7, §9.1–§9.2, §10, §12 (Python).
**Goal:** `server/ai/` implements every function in SPEC §7 exactly. It never touches the database and never imports anything from `server/api/` or `server/store/`. Work only inside `server/ai/` and `server/tests/ai/`.

## Reuse (if the old Streamlit repo is available in `CAICC #2`)
- Copy into `server/ai/`:
  - `core/llm.py`, `core/prompts.py`, `core/schemas.py`;
  - `services/extract.py`, `media.py`, `transcribe.py`, `summarize.py`, `figures.py`, `charts.py`, `meeting.py`;
  - the AI parts of `services/forum.py` → `forum_ai.py`.
- Keep their tests and make them pass in the new place.
- Then remove every database and Streamlit dependency from this code:
  - calls are recorded into a per-request `ai_calls` list instead of the DB;
  - `st.cache_resource` becomes `functools.lru_cache`;
  - figures are written to `DATA_DIR/figures/<job_id>/` and returned as paths.
- **If that code is not available:** build these modules from SPEC §9–§10 instead and tell me first (this adds about one day).

## Tasks
1. **LLM client** (SPEC §9.1): roles → the 4 models only; a 401 raises `ModelScopeAuthError` with no retry; `health()` reports `invalid_token`.
2. **`summarize()`** (SPEC §10.1, §10.5, §10.6): all stages, calling `on_stage(name)` when each starts. Heavy work stays synchronous; the job runner in P3 puts it on the thread pool.
3. **`transcribe()`** (SPEC §9.2, §10.2):
   - media → probe → whisper → translate → meeting;
   - transcript files: `.srt`/`.vtt` → timed segments, `.txt` → sentences, then the same translate → meeting stages;
   - with `ENABLE_TRANSCRIPTION=false`, media raises `AIError("transcription_disabled")`; transcript files still work.
4. **Duration probe:** `media_too_long` with the real duration in minutes.
5. **Forum AI** (SPEC §10.4): similar, tags, moderate (fail open), hint (never the final answer).
6. **`scripts/smoke_test.py`** (SPEC §12) against the real API.

## Done when
- [ ] `pytest server/tests/ai` (fake LLM) passes, including the chart-safety cases, transcript parsing and `ENABLE_TRANSCRIPTION=false`.
- [ ] Smoke test table: 4 models OK with latency, VISION formula image OK, whisper loads and reports its source.
- [ ] One real run of each function on sample files (a PDF with formulas, a PPTX with a repeated logo, a 1-minute speech clip, an .srt file). Report:
  - candidates → filtered → selected figures;
  - charts drawn;
  - VISION calls;
  - seconds per stage.
- [ ] `grep` shows no `streamlit`, no `sqlite3`, no `openai` import outside `server/ai/`, and no model ID outside `llm.py`/`config.py`.
