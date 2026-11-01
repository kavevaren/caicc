# P0 · Prove the platform (Sat 31 Oct, ≤ 3 h)

**Read:** `prompts/_RULES.md`, `docs/SPEC.md` §2, §3, §4.1, §13.
**Goal:** before building anything real, prove that one Docker image with a Python FastAPI server and a React page runs on ModelScope Studio on the free CPU, and measure the Studio limits we depend on.

## Tasks
1. **Inspect the folder and restructure it.**
   - The folder has a P0 draft from the old v4 plan: `gateway/` (Go), `engine/` (Python), `web/` (React).
   - Move `gateway/` to `arsip/gateway-go/` (history only; never deployed). Do not delete it.
   - Create `server/` (SPEC §4) and move the useful parts of `engine/main.py` into it (ModelScope probe, whisper loader). Then move `engine/` to `arsip/engine-v4/`.
   - Remove from `web/` everything that only served live captions: the PiP test and the WebSocket echo.
2. **Hello stack:**
   - `server/main.py` (FastAPI, `0.0.0.0:${PORT:-7860}`, one worker):
     - serves `web/dist` with SPA fallback;
     - `GET /api/health` → `{server, modelscope, whisper, version}`: one tiny FAST call to ModelScope in a background thread (cached), reporting `ok` / `invalid_token` / `unreachable`; whisper `idle` / `loading` / `ready` / `disabled`;
     - `POST /api/probe/upload` (stores nothing, returns the byte count) to measure the Studio's upload limit;
     - `GET /api/probe/sse` sending one event per second for 20 s, to check whether the Studio proxy buffers SSE;
     - `POST /api/probe/whisper` loads whisper `base` once (only when `ENABLE_TRANSCRIPTION=true`).
   - `web/` (React + Vite + TypeScript + motion, Vite `base: "./"`, relative API URLs):
     - one page with the AtomLoader (the logo's two ellipses counter-rotating);
     - the health JSON;
     - an SSE test that shows the arrival time of each event;
     - an upload test (10, 50, 100, 200 MB generated blobs);
     - a mic level meter (`getUserMedia` + `AudioContext`);
     - a `localStorage` write/read test;
     - a "Buka di tab baru" link to `PUBLIC_APP_URL`.
3. **Packaging (SPEC §13):** the 2-stage `Dockerfile`, `ms_deploy.json` (`sdk_type: docker`, port 7860), `.dockerignore`, `.env.example` (variables from SPEC §4.1 only; token link `https://modelscope.ai/my/access/token`), `server/requirements.txt` with pinned versions.
4. **Deploy to a separate test Studio** (not the final one):
   - in the deployment settings, choose the **free CPU** option and write its exact name into `ms_deploy.json` `resource_configuration`. Never choose GPU, xGPU or a paid option;
   - the token goes in the Studio Secrets. Locally, `MODELSCOPE_TOKEN` and `APP_SECRET_KEY` are already in `.env`; never copy their values into a prompt, doc, log or test.

## Done when
- [ ] `gateway/` and `engine/` are in `arsip/`; `server/` and `web/` build; no Go is left in the image.
- [ ] The image builds locally and on the Studio. Report the image size, build time on the Studio and cold-start time (container start → `/api/health` answers).
- [ ] Health shows `server ok · modelscope ok · whisper idle` on the deployed URL (with the real token), and `whisper ready` after the whisper probe.
- [ ] The free CPU option name, its vCPU and RAM, recorded in `docs/PROGRESS.md`.
- [ ] A results table, **inside the Studio page** vs **on the direct app URL**, for: SSE (events arrive one per second, or buffered), largest accepted upload, mic, `localStorage`.
- [ ] Peak RAM of the container idle and with whisper `base` loaded.
- [ ] Whether `/data` is writable and survives a restart.

**Stop immediately if the Studio does not accept Docker.** Report what it offers; we will switch to the Gradio fallback in SPEC §13.
