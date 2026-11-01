# P1 · Contract, schema and skeleton (Sat 31 Oct night, ≤ 4 h)

**Read:** `_RULES.md`, SPEC §3–§7, §12, §13, and the P0 report in `docs/PROGRESS.md`.
**Goal:** write the contract and the skeleton that let the AI modules (P2), the API (P3) and the web app (P4) be built in parallel without drifting.

## Tasks
1. **Apply the P0 findings first:**
   - if the Studio proxy buffers SSE, make polling the default for jobs and keep SSE optional;
   - if uploads above some size fail, set `MAX_UPLOAD_MB` to the largest size that worked;
   - if RAM with whisper is close to the limit, set the default `WHISPER_MODEL` to `tiny`.
2. **`contracts/openapi.yaml`**: every public endpoint in SPEC §6, with:
   - request and response schemas;
   - error codes per endpoint;
   - `bearerAuth`;
   - the SSE event shapes and the stream-ticket flow.

   Include the bug-driven rules as schema constraints:
   - question title 10–150 characters;
   - event `end_at` after `start_at`;
   - `accept_terms` must be true.
3. **SQL migrations:** `server/migrations/001_init.sql` with every table, index, FTS5 table and sync trigger in SPEC §5. Explicit column lists everywhere.
4. **Server skeleton** (SPEC §4):
   - `server/config.py` (SPEC §4.1, with the `DATA_DIR` fallback);
   - `server/store/db.py`: per-thread connections, pragmas, `write()` with the process-wide lock, migrations on startup;
   - `server/api/errors.py`: error JSON and global exception handlers (no traceback ever reaches the browser);
   - `server/api/deps.py`: Bearer auth dependency and the in-memory rate limiter;
   - one empty router per area from SPEC §6, returning 501 `not_implemented`;
   - `server/ai/__init__.py` exposing the SPEC §7 function signatures, each raising `NotImplementedError`, plus a `FakeLLM` for tests.
5. **Generated types and mocks:**
   - `web/src/lib/api-types.ts` from `openapi.yaml` (`openapi-typescript`);
   - an MSW mock layer (`web/src/mocks/`) returning realistic Indonesian sample data (the mockup's data), so P4 can work before the API exists.
6. **Project tooling:**
   - `Makefile` (`dev`, `test`, `lint`, `build`, `e2e`, `compliance`, `docker`);
   - `scripts/compliance.py` (SPEC §12 Compliance), already passing on the skeleton;
   - `README.md` stub with the architecture diagram from SPEC §3.2;
   - `docs/PROGRESS.md` with the sections from `_RULES.md`.
7. **Contract tests wired:**
   - Python: schemathesis against `openapi.yaml` on the FastAPI app;
   - TS: `tsc` on the generated types.
8. **Docs:** make sure `docs/SPEC.md`, `docs/design/DESIGN.md`, `docs/design/dashboard-mockup.html` and the brand SVGs in `assets/brand/` are the current versions.

## Done when
- [ ] `openapi.yaml` validates (`redocly lint` or equivalent), and every endpoint in SPEC §6 is present.
- [ ] `001_init.sql` applies twice on an empty DB without error.
- [ ] `uvicorn server.main:app` starts with an empty `DATA_DIR`, creates the DB and answers `/api/health`.
- [ ] `npm run dev` shows the mock-backed app shell with no server running.
- [ ] `make compliance` passes.
- [ ] Report: the endpoint count, and anything in the SPEC you found ambiguous.
