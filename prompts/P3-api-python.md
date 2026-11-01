# P3 · API, data and jobs in Python (Sun 1 Nov – Mon 2 Nov) · lane B, can run in parallel with P2 and P4

**Read:** `_RULES.md`, SPEC §3, §5, §6, §8 (rules per page), §9.3–§9.4, §11, §12 (Python), §13.
**Goal:** the FastAPI app implements `contracts/openapi.yaml`, owns SQLite and all product rules, and runs jobs. Work in `server/api/`, `server/store/`, `server/jobs/`, `server/domain/`, `server/main.py`, `server/seed.py` and their tests. Never edit `server/ai/` (lane A); call it only through the SPEC §7 functions, using `FakeLLM` until P2 is done.

> **Scope cut (see `_RULES.md`):**
> - Order: task 1, task 2, auth, dashboard, task 4 (F1 summaries), then forum + points + leaderboard, then events in local mode.
> - Task 3: skip notifications, and skip Google OAuth and Calendar (leave them returning 501).
> - Task 4: polling only; skip the SSE stream; `/api/transcripts` accepts transcript files only.
> - "Done when": skip schemathesis and the 20-user load check; the job only needs to show its stages over polling.
> - Gate, Mon 2 Nov 12:00: only auth, dashboard and F1 must be green.

## Tasks
1. **App and startup (`server/main.py`):**
   - config from the environment (SPEC §4.1);
   - lifespan: migrations → seed if the DB is empty → ModelScope health check in the background;
   - `web/dist` with SPA fallback: long cache for hashed assets, no cache for `index.html`;
   - `python -m server.seed` (idempotent, SPEC §12).
2. **Cross-cutting:**
   - request ID and logging (no secrets, no prompt text);
   - **exception handlers → error JSON**;
   - Bearer auth (sha256 token lookup);
   - per-user rate limits;
   - body size limits (`MAX_UPLOAD_MB`, SPEC §11).
3. **Routers per area** (SPEC §6), with the rules from §8 and §11 implemented here:
   - auth (bcrypt cost 12; generic login error; `terms_required`), plus onboarding;
   - the dashboard aggregate: one query set returning real data for all blocks;
   - forum:
     - FTS5 search;
     - similar questions: FTS5 top 10 → `ai.forum_similar`;
     - tags, moderation and hints → `ai`;
     - votes (unique, no self-votes), best answer, follow, attachments;
   - points ledger with reversals; leaderboard windows (Monday 00:00 Asia/Jakarta);
   - notifications created on action, with `event_soon` / `rank_change` computed on dashboard load;
   - events:
     - explicit column INSERTs;
     - `end_at` > `start_at`, defaulting to start + 1 h;
     - `.ics` (RFC 5545) and the template link;
     - suggestions accept/dismiss;
   - Google OAuth and Calendar with `httpx` (SPEC §9.3); tokens encrypted with AES-GCM.
4. **Jobs (`server/jobs/`):**
   - `POST /api/summaries` and `/api/transcripts` store uploads (uuid names) and create a job, returning in < 2 s;
   - a `ThreadPoolExecutor(JOB_WORKERS)` runs `ai.summarize` / `ai.transcribe`; extra jobs wait in the queue;
   - `on_stage` updates `jobs.stage` and publishes to the progress hub;
   - `GET /api/jobs/{id}/stream?ticket=` (SSE with `X-Accel-Buffering: no` and a 15 s heartbeat) and `GET /api/jobs/{id}` for polling;
   - the result is stored: document, figures, suggestions, `ai_calls`;
   - `AIError` codes are mapped to the API error codes.

## Acceptance (from the 30 Oct browser test; each needs a pytest)
1. ModelScope 401 → `/api/health` reports `modelscope: invalid_token`; AI endpoints return 503 `modelscope_token_invalid`.
2. A question title under 10 or over 150 characters → 422 with `title_length`.
3. Saving an event succeeds, with a test asserting the exact INSERT column list.
4. An exception in any route returns the error JSON; the traceback goes only to the log.
5. Register without terms → `terms_required`.
6. `end_at` ≤ `start_at` → 422 `end_before_start`.

## Done when
- [ ] `pytest` and `ruff` pass; schemathesis is green for every endpoint.
- [ ] Load check: 20 concurrent users hitting dashboard + forum list (e.g. with `hey` or `locust`) at p95 < 300 ms on the free CPU Studio, with no "database is locked" errors.
- [ ] A job runs end to end with the real `ai` modules and shows its stages over SSE **and** over polling, on the deployed test Studio.

**Gate, Mon 2 Nov 12:00.** If auth, events and forum are not green by then, stop and tell me.
