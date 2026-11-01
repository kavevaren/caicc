# Orvina progress

## Current phase
- Phase: P1 Contract, schema and skeleton
- Task: 5 of 8, client contract types + MSW mocks
- Status: in progress
- Last change: server skeleton verified end-to-end (fresh DATA_DIR, double migration, health/401/501/SPA); fixes: double /api prefix removed from 12 routers, HTTPException -> contract error JSON, python-multipart 0.0.20 pinned; contracts/openapi.yaml: 501 on all 53 ops + 7 scalar quotes (valid YAML, PyYAML-checked); one-shot scripts/_verify_p1t4.py + scripts/_check_db.py
- Next step: P1 task 5 — web devDeps openapi-typescript + msw, generate web/src/lib/api-types.ts from contracts/openapi.yaml, MSW mock layer web/src/mocks/ with the mockup's Indonesian data, wire into web/src/main.tsx so `npm run dev` runs without a server, then `npm run build` directly in web/ (no temp copy needed: the new path has no "#"). Note: web/src/lib/api-types.ts, web/src/mocks/{data,handlers,browser}.ts, web/src/main.tsx, web/tsconfig.json and web/package.json were already changed at 15:35–15:43, after the last checkpoint; check and finish them instead of starting over

## Done
- P1 task 1: done, P0 findings applied: deploy not yet done, so SPEC defaults stand (SSE with polling fallback, MAX_UPLOAD_MB=200, WHISPER_MODEL=base); PROBE_MODEL added for the Step-3.5-Flash outage; will adjust from the P0 results table after deploy
- P1 task 2: done, contracts/openapi.yaml: 45 endpoints (health, auth, me, subjects, dashboard, jobs, F1, F2, F3, F4, points, notifications, files), bearerAuth, SSE event shapes + stream-ticket flow, per-endpoint error codes, constraints (title 10-150, end_at > start_at, accept_terms=true)
- P1 task 3: done, server/migrations/001_init.sql: all SPEC §5 tables with explicit columns, indexes, FTS5 external-content table + 3 sync triggers, IF NOT EXISTS everywhere (double-apply safe)
- P1 task 4: done, server skeleton verified on a fresh DATA_DIR (C:\tmp\orvina-p1): migration 001 applied once, restart no-op (schema_version=1, 28 tables incl. FTS shadows); /api/health 200 (server/modelscope ok, whisper idle), /api/me 401 unauthenticated without token and 501 not_implemented with a fake session, /api/documents/1 501, SPA / + fallback 200, unknown /api/* 404 in contract error JSON. Fixes found by the run: python-multipart 0.0.20 pinned (Form/UploadFile stubs), double /api prefix removed from 12 routers (they matched /api/api/...), HTTPException handler added so every error is {"error":{code,message_key}}. contracts/openapi.yaml: "501" NotImplemented added to all 53 operations + 7 unquoted `: ` scalars fixed (file now parses, PyYAML 6.0.3). Verification: scripts/_verify_p1t4.py ALL PASS (8/8), scripts/_check_db.py
- P0 task 1: done, restructured: gateway/ -> arsip/gateway-go/, engine/ -> arsip/engine-v4/, server/ created, PiP + WebSocket echo removed from web/ (new App.tsx)
- P0 task 2: done (locally), hello stack: server/main.py (SPA fallback, /api/health cached probe, probe upload/sse/whisper/config), server/ai/probe.py (ModelScope probe + whisper loader; openai only in server/ai/), web P0 page (AtomLoader, health JSON, SSE arrival table, 10/50/100/200 MB upload buttons, mic meter, localStorage, "Buka di tab baru"); local build OK (tsc + vite, via temp copy — see blocker), local smoke OK: health `server ok · modelscope ok (DeepSeek probe 1595 ms) · whisper idle`, SPA + fallback 200, SSE ticks 1/s, uploads 1 MB + 50 MB intact
- P0 task 3: done, packaging: 2-stage Dockerfile (node:20-slim build, python:3.10-slim runtime, fonts-noto-cjk, pinned deps, whisper pre-download `|| true`), ms_deploy.json (sdk docker, port 7860), .dockerignore, .env.example, server/requirements.txt pinned (fastapi 0.116.2, uvicorn 0.35.0, openai 1.109.1, faster-whisper 1.2.1)

## Not done / blocked
- P0 task 4 (deploy to a test Studio): needs the ModelScope Studio console (create Studio, pick free CPU option, set secrets, watch build). Prepared to be executable as soon as the user opens the console.
- Local `docker build`: no Docker on this machine (checked 2026-10-31). Studio build will be the first real image build.
- `vite build` fails in a path containing "#": Rollup treats "#" as a URL fragment ("Could not resolve ./App"). The same source builds fine from a # -free path (388 modules, JS 263 kB / gzip 85.7 kB). Docker builds are unaffected (container paths). Local dev needs a # -free copy or a renamed folder. — RESOLVED 2026-10-31 16:05: project moved to `C:\Users\Lenovo\Documents\CAICC4` (no "#"); build directly in web/.
- whisper `base` load locally: FAILED — this machine's network drops HF connections (WinError 10054, 5/5 retries exhausted). HF API itself is reachable (200 OK on metadata). Needs re-check on the Studio (image pre-downloads the model at build time, `|| true`). — RESOLVED 2026-10-31: download succeeded on retry and the model is now cached locally (load ~20 s); P0 local smoke showed whisper idle -> ready(base). Studio pre-download still to verify.
- `stepfun-ai/Step-3.5-Flash` (the FAST model) returns 400 "no provider supported" on the ModelScope API as of 2026-10-31 ~15:00; GLM-5.2 (3687 ms), DeepSeek-V4-Pro-0813 (999 ms) and Qwen3.8-27B (1045 ms) all OK with the real token. Added `PROBE_MODEL` env (default = FAST, only the 4 allowed models accepted) so the health probe can show `ok` even while Step is down. The FAST role in P2 pipelines will hit this if it persists at competition time — flag to organizers / monitor.
- Free-CPU option name: API guesses 404; must be read from the Studio deployment UI. `ms_deploy.json` currently says `2vcpu-16g` (from the old v4 plan) — VERIFY before deploy.

## Assumptions
- Project root is `C:\Users\Lenovo\Documents\CAICC4` since 2026-10-31 16:05 (moved from `CAICC #3`; all 7017 files verified identical by SHA-256; `.venv` recreated with the identical 44 packages; `CAICC #3` kept unchanged as a backup — do not work there).
- Dev machine: Python 3.14.4, Node v26.8.2, npm 11.19.1, no Docker. Local venv `.venv` has the pinned P0 deps (verified importable).
- P0 probe page uses inline Indonesian strings; locales come with P4.
- `/api/probe/config` is P0-only (exposes PUBLIC_APP_URL to the page); removed in P1.
- `PROBE_MODEL` is an extra env var beyond SPEC §4.1 (operational knob; default keeps SPEC behavior).

## Manual checks for the developer
- In the Studio deployment settings: choose the FREE CPU option only; copy its exact name into `ms_deploy.json` `resource_configuration`; record vCPU/RAM here.
- Put `MODELSCOPE_TOKEN`, `APP_SECRET_KEY` (and `PUBLIC_APP_URL` after deploy) in the Studio Secrets. Never copy values into prompts/docs/logs.
- After deploy, on BOTH the Studio page and the direct app URL, run and record: SSE (1/s or buffered?), largest accepted upload (10/50/100/200 MB), mic, localStorage, cold-start time (container start -> /api/health), peak RAM idle and with whisper loaded, and whether /data survives a restart.

## P0 results table (to fill after deploy)
| Check | Studio page (iframe) | Direct app URL |
|---|---|---|
| Cold start (start -> /api/health) | | |
| SSE: 1/s or buffered | | |
| Largest accepted upload | | |
| Mic (getUserMedia) | | |
| localStorage | | |
| Peak RAM idle | | |
| Peak RAM with whisper base | | |
| /data writable / survives restart | | |

## Checkpoint log
- 2026-10-31 14:44 · Qwen/Qwen3.8-27B · P0 task 1 · created docs/PROGRESS.md from template (did not exist) · tests: not run · next: restructure folder (arsip/, server/, web cleanup)
- 2026-10-31 15:05 · Qwen/Qwen3.8-27B · P0 task 1+2 · restructured (arsip/gateway-go, arsip/engine-v4, server/); wrote server main.py + ai/probe.py + pinned requirements; rewrote web P0 page (no PiP/WS) · tests: not run · next: npm install + build, then local server smoke test
- 2026-10-31 15:35 · Qwen/Qwen3.8-27B · P0 task 2+3 · local smoke pass (health ok via PROBE_MODEL=DeepSeek, SSE 1/s, uploads 1/50 MB, SPA); packaging done (Dockerfile, ms_deploy.json, .dockerignore, .env.example); found Step-3.5-Flash down on ModelScope, whisper HF download flaky locally, vite "#" path issue · tests: local pass / Studio not run · next: deploy to test Studio (developer), fill results table
- 2026-10-31 15:30 · Qwen/Qwen3.8-27B · P1 task 4 · server skeleton verified: fresh DATA_DIR, migration once + restart no-op, health/401/501/SPA/404-JSON all pass (scripts/_verify_p1t4.py 8/8); fixed double /api prefix (12 routers), HTTPException -> contract error JSON, pinned python-multipart 0.0.20; openapi.yaml: 501 on all 53 ops, 7 scalar quotes, valid YAML (PyYAML) · tests: ALL PASS locally · next: P1 task 5 — openapi-typescript + msw, generate api-types.ts, MSW mocks (mockup data), wire main.tsx, rebuild via temp copy
- 2026-10-31 15:32 · Qwen/Qwen3.8-27B · P1 task 5 · pre-install checkpoint: read mockup data (Aldo/128 pts/rank 4, 3 subjects, 4 events, 4 questions, top5, 3 reminders, 3 recent) + contract response shapes for all 43 paths; starting `npm i -D openapi-typescript msw` in web/ · tests: not run · next: msw init, generate api-types.ts, write web/src/mocks/, wire main.tsx
- 2026-10-31 16:05 · housekeeping by the developer's assistant (no code changed) · project moved from `CAICC #3` to `CAICC4` (no "#" in the path); 7017 files verified identical; `.venv` recreated (same 44 packages) · tests: `npm run build` in web/ now runs without the "#" error, but tsc fails in the unfinished task-5 files: web/src/mocks/data.ts uses `S.Document`, `S.Figure`, `S.Job`, `S.Dashboard`… where `S` is a type, not a namespace (TS2713, use `S["Document"]` style), and web/src/mocks/handlers.ts lines 161, 391 have implicit `any` (TS7006); Python deps import OK · next: fix those tsc errors, then finish P1 task 5

## P0 report (2026-10-31, model Qwen/Qwen3.8-27B, prompt P0-platform-probe.md)
1. **Files changed**
   - `arsip/gateway-go/`, `arsip/engine-v4/` — moved (history, never deployed)
   - `server/main.py` — P0 hello stack: SPA fallback, /api/health, probe upload/sse/whisper/config
   - `server/ai/__init__.py`, `server/ai/probe.py` — ModelScope probe (background thread, 5-min cache) + whisper loader; `openai` stays inside `server/ai/`
   - `server/requirements.txt` — pinned: fastapi 0.116.2, uvicorn[standard] 0.35.0, openai 1.109.1, faster-whisper 1.2.1
   - `web/src/App.tsx` — P0 probe page (SSE arrival table, 10/50/100/200 MB upload, mic meter, localStorage, "Buka di tab baru"); PiP + WebSocket echo removed
   - `web/vite.config.ts` — `base: "./"`, /api proxy only; `web/index.html` — relative entry + icon; `web/public/orvina-app-icon.svg` — favicon
   - `Dockerfile` — 2-stage per SPEC §13; `ms_deploy.json` — sdk docker, port 7860; `.dockerignore`; `.env.example` — SPEC §4.1 vars + PROBE_MODEL
2. **Test output / build**
   - Python: local smoke on `.venv` (pinned deps): `/api/health` → `{"server":"ok","modelscope":"ok"(1595 ms, PROBE_MODEL=deepseek), "whisper":"idle"→"ready"(base)}`; SSE ticks 1 per second (5/5 in first 5 s); uploads 1 MB + 50 MB byte-exact; SPA `/` + fallback `/forum/q/123` → 200.
   - Web: `tsc --noEmit` clean; `vite build` OK (388 modules; JS 263 kB, gzip 85.7 kB; CSS 2.4 kB) — via temp copy because Rollup cannot resolve paths containing "#" (see risks).
   - Docker: not built locally (no Docker on this machine); first build will be the Studio's.
3. **Acceptance (P0 "Done when")**
   - gateway/ and engine/ in arsip/, server/ and web/ build, no Go in image — **done** (no Go anywhere in the new image; arsip is docker-ignored)
   - image builds locally and on Studio — **not done**: no Docker locally; Studio build pending deploy
   - health `server ok · modelscope ok · whisper idle` on the deployed URL — **pending deploy** (verified locally with the real token; `whisper ready` after the probe)
   - free CPU option name + vCPU/RAM in this file — **pending** (must be read from the Studio UI; `ms_deploy.json` placeholder `2vcpu-16g` from the old plan — VERIFY)
   - results table Studio page vs direct URL — **pending deploy** (empty table above)
   - peak RAM idle / with whisper — **pending deploy**
   - `/data` writable + survives restart — **pending deploy**
4. **Screenshots** — none yet; the page needs the deployed URL (Studio page + direct URL).
5. **Risks and open questions**
   - `stepfun-ai/Step-3.5-Flash` (FAST role) is down on the ModelScope API ("no provider supported", observed 2026-10-31 ~15:00). P2 pipelines use FAST for map/translate/similar/tags. If it stays down at competition time the FAST role has no replacement inside the 4-model rule — ask the organizers.
   - Local network to Hugging Face drops connections (WinError 10054); whisper download only succeeded on retry with cache. The image pre-downloads whisper at build time (`|| true`) — verify on the Studio.
   - Vite/Rollup cannot build in a folder path containing "#" — the Studio build is unaffected (container path `/app`); local dev needs a #-free copy.
   - The 400 "no provider supported" maps to `unreachable` in health (schema has no other status).
6. **Proposed next step** — deploy this folder to a separate test Studio (free CPU only) and fill the results table; meanwhile P1 proceeds with the SPEC defaults (SSE + polling fallback, MAX_UPLOAD_MB=200, WHISPER_MODEL=base) and adjusts from the table when it is filled.

## Prompt log
- 2026-10-31 · P0 · Qwen/Qwen3.8-27B · prompt: P0-platform-probe.md · tasks 1-3 done locally; task 4 (deploy) blocked on the Studio console; findings: Step-3.5-Flash "no provider supported", local HF drops, Rollup "#" path issue · fixes: PROBE_MODEL env, probe exception logging, whisper error surfaced in probe response, BlobPart type fix, relative index.html entry · test output: local health/SSE/upload smoke pass; web build pass (temp path) · screenshots: not yet (need deployed URL)
