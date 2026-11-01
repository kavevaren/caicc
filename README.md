# Orvina prompt pack v5 (Python + React, built for ModelScope Studio)

Updated 31 Oct 2026. This pack replaces v4. Changes from v4:
- **No Go gateway.** One Python FastAPI process serves the React build, the API, SQLite, jobs and the AI, so the Studio runs one container with one process on the free CPU.
- **No live captions** (Presentasi langsung, floating window, WebSocket). F2 keeps Rekam and Unggah, and can also import transcript files (.srt, .vtt, .txt).
- **faster-whisper is at risk** under the competition rules (only 4 models allowed). Every feature must work with `ENABLE_TRANSCRIPTION=false`; P6 decides based on the organizers' answer.

The old prompt pack is in `prompts/prompt.zip` as prompting-history evidence; do not run it.

## Architecture in one line
React/TypeScript animated UI → Python FastAPI server (API, accounts, forum, points, calendar, jobs, SQLite, 4 ModelScope models, documents, figures, charts). One Docker image, one process on ModelScope Studio. Details: `SPEC.md` §3 and §13.

## Files

| File | What it is | Goes into the repo as |
|---|---|---|
| `SPEC.md` | Product, rules, architecture, data, API, pipelines, quality bar, deploy | `docs/SPEC.md` |
| `DESIGN.md` | UI tokens and the animated atom system, page by page | `docs/design/DESIGN.md` |
| `design/dashboard-mockup.html` | Approved static Dashboard (open it in a browser) | `docs/design/dashboard-mockup.html` |
| `BRAND.md`, `brand/` | Name, tagline, logo SVGs | `assets/brand/` |
| `FEATURES.md` | Feature list (for the README, pitch and demo video) | — |
| `prompts/_RULES.md` | Rules the agent follows in every phase | `prompts/` |
| `prompts/P0` … `P6` | The build, one phase per prompt | `prompts/` |

## How to run it

1. Use Claude Code (or OpenCode) configured with one of the 4 approved models, as in STEP C of the participant guide. Check that the model name is visible in the agent, and take screenshots as you go.
2. First message to the coding agent:
   > Read `prompts/_RULES.md`, `SPEC.md`, `DESIGN.md` and `design/dashboard-mockup.html`. Then do `prompts/P0-platform-probe.md` only, and report.
3. After each report, check the result in the browser, then send the next prompt: "Lanjut: `prompts/P1-…md`".
4. **P2, P3 and P4 can run at the same time** in three agent sessions (you and your friend), because P1 fixes the contract. Each lane touches only its own folders:
   - P2: `server/ai/`;
   - P3: `server/api/`, `server/store/`, `server/jobs/`, `server/domain/`, `server/main.py`;
   - P4: `web/`.

| Phase | Lane | When | Gate |
|---|---|---|---|
| P0 platform probe | — | Sat 31 Oct afternoon | Stop if the Studio does not accept Docker (Gradio fallback, SPEC §13) |
| P1 contract + skeleton | — | Sat 31 Oct night | |
| P2 AI modules (Python) | A | Sun 1 Nov | |
| P3 API, data, jobs (Python) | B | Sun 1 – Mon 2 Nov | **Mon 12:00:** auth, events and forum green |
| P4 web + Dashboard (TS) | C | Sun 1 – Mon 2 Nov | |
| P5 feature pages + e2e | — | Mon 2 – Tue 3 Nov | **Tue 12:00 go/no-go:** otherwise submit the old Streamlit app (`CAICC #2`) |
| P6 polish + ship | — | Tue 3 Nov → Wed 4 Nov, 16:00–23:59 WIB | |

**Cut order if time runs out:**
1. scroll-linked dashboard effects;
2. forum video answers;
3. charts;
4. Google OAuth (keep local mode);
5. Rekam in the browser (keep Unggah).

Never cut: the 4-model rule, the week atom with zoom, F1, F2 upload.

## Before you start
- A **valid ModelScope token** in `.env` and in the Studio Secret (the 30 Oct test failed with 401 on every AI call).
- **Ask the organizers in the WhatsApp group** whether faster-whisper (open-source, CPU) is allowed, and keep a screenshot of the answer. Write the answer under "Assumptions" in `docs/PROGRESS.md`.
- Keep the old Streamlit folder untouched until Tuesday's gate passes.
- Every phase appends to the "Prompt log" section of `docs/PROGRESS.md`. Keep the agent screenshots with the model name visible; they are submission evidence.
