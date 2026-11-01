# Agent rules (read once; every phase prompt assumes them)

You build **Orvina** from `docs/SPEC.md` (functional + architecture) and `docs/design/DESIGN.md` (UI + motion). The static target is `docs/design/dashboard-mockup.html`. If anything here conflicts with a phase prompt, the phase prompt wins; if the SPEC is unclear, ask before coding.

## Non-negotiable (SPEC §2; any break disqualifies us)
1. **LLMs:**
   - Only `zai-org/GLM-5.2`, `deepseek-ai/DeepSeek-V4-Pro-0813`, `stepfun-ai/Step-3.5-Flash` and `Qwen/Qwen3.8-27B`, via `https://api-inference.modelscope.ai/v1`.
   - Only `server/ai/llm.py` calls them. `openai` is imported nowhere outside `server/ai/`.
2. **No other AI services:** no proprietary AI service and no Web Speech API, anywhere. Speech-to-text is faster-whisper on CPU only, behind `ENABLE_TRANSCRIPTION`, and **every feature must still work with `ENABLE_TRANSCRIPTION=false`** (SPEC §2.3).
3. **No training, no fine-tuning, no GPU.** Free CPU tier only.
4. **Secrets:** from environment variables only. Never in code, logs, tests, the web bundle, prompt files or docs. The real values live only in `.env` (git-ignored, never shared) and in the Studio Secrets.
5. **Code authorship:** you write all code. Never write the `MANUAL` marker.
6. **No new dependencies without asking.** Only what SPEC §3.1 lists.

## Way of working
- **Structure (SPEC §3–§4):**
  - TypeScript in `web/`, Python in `server/`, SQL in `server/migrations/`.
  - One backend process: FastAPI on `0.0.0.0:7860`, one uvicorn worker. No Go, no second service, no WebSocket.
  - `contracts/openapi.yaml` is the source of truth between `web/` and `server/`. Change the contract first, then both sides.
  - Blocking work (AI calls, file parsing, whisper) never runs on the event loop.
  - Every SQLite write goes through `store.db.write()`.
- **ModelScope Studio first (SPEC §13):** relative URLs only, Bearer token in `localStorage`, SSE with polling fallback, fast startup, `DATA_DIR` fallback to `/tmp/orvina`. Anything that only works on localhost is not done.
- **Before saying "done":**
  - run `make test lint build` (pytest/ruff, vitest/eslint/tsc);
  - **open the affected page in a browser and click through it.** Tests passing is not done.
- **Every bug fix gets a regression test** in the language where the bug lived.
- **User-facing errors** are translated JSON (`{"error":{"code","message_key"}}`) shown with "Coba lagi". A stack trace must never reach the browser.
- **Text:** every UI string comes from `web/src/locales/{id,en,zh}.json`. No emoji. Sentence case.
- **Checkpoints:** follow the "Checkpoints (mandatory)" rules and the template in `AGENTS.md`.
- **Progress tracking (the only record):**
  - This project does not use git. Never run `git init`, `add`, `commit`, `status`, `log` or `tag`. Where a prompt mentions a commit or a tag, skip that step and write "skipped: no git".
  - Track everything in `docs/PROGRESS.md` and nowhere else. Sections:
    - "Current phase": the phase, the task number in progress, and the exact next step;
    - "Done": one line per finished task, as "P<n> task <n>: done, <short note>";
    - "Not done / blocked": anything skipped or failing, with the reason;
    - "Assumptions" and "Manual checks for the developer";
    - "Prompt log".
  - Update it after every numbered task inside a phase, in a few lines, before starting the next task. At the end of each phase, append the phase report.
  - Write the exact next step every time, so a new session can resume from this file alone.
- **Evidence (50% of our score is ModelScope usage and prompting iteration):** after each phase, append to the "Prompt log" section of `docs/PROGRESS.md`:
  - the date and phase;
  - the model you are running on (exact ID);
  - the prompt you received (file name);
  - your summary;
  - the fixes;
  - test output and screenshot paths.
- **Ambiguity:** ask one precise question instead of guessing on anything that is costly to undo.

## Report format (end of every phase: write it into `docs/PROGRESS.md`, then stop and wait for "lanjut")
1. **Files changed** (one line each, with the reason).
2. **Test output** (each language) and build result.
3. **Acceptance:** one line per "Done when" item: done / not done + why.
4. **Screenshots or recordings** where the phase asks for them.
5. **Risks and open questions.**
6. **Proposed next step.**
