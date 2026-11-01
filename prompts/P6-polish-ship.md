# P6 · Polish, compliance, deploy, evidence (Tue 3 Nov → submit Wed 4 Nov, 16:00–23:59 WIB)

**Read:** `_RULES.md`, SPEC §2, §12, §13.
**Goal:** a stable public Studio, a clean project, and complete evidence for the judges.

## Tasks
1. **Remove leftovers:** mocks from the production build, unused deps, leftover test output. `arsip/` stays out of the image and out of the submission zip. The old Streamlit app stays only in its own folder (`CAICC #2`), never in this project.
2. **Transcription decision.** Read "Assumptions" in `docs/PROGRESS.md` for the organizers' answer on faster-whisper:
   - confirmed allowed in writing → keep it, and put the screenshot of the answer in `docs/evidence/`;
   - not allowed or no answer → set `ENABLE_TRANSCRIPTION=false` in the Studio, remove `faster-whisper` from `server/requirements.txt` and the pre-download from the `Dockerfile`, and rebuild.
3. **`make compliance` green.** It fails on:
   - any non-allowed model ID, or `openai` imported outside `server/ai/`;
   - a forbidden AI domain, or `SpeechRecognition` / `webkitSpeechRecognition`;
   - a token-like string;
   - emoji in UI strings;
   - more than 30 `MANUAL` lines.

   Print the `MANUAL` count.
4. **Full test run:**
   - pytest, ruff, vitest, eslint, tsc, build;
   - Playwright e2e of the full loop **on the deployed Studio URL**;
   - Lighthouse on the Dashboard (Performance ≥ 85, Accessibility ≥ 95).
5. **Studio:**
   - final Docker deploy on the **free CPU** option;
   - Secrets set (`MODELSCOPE_TOKEN`, `APP_SECRET_KEY`, Google vars if used, `PUBLIC_APP_URL`);
   - visibility **Public**;
   - seed loaded; health all green;
   - restart the Studio once and confirm the app comes back with the seed.

   A 20-user load check (dashboard, forum, one summary job) without errors.
6. **README:**
   - Orvina lockup, one-paragraph pitch, screenshots;
   - architecture (SPEC §3.2) with the language-per-layer table and why;
   - setup (Docker + `make dev`), environment variables, Studio Secrets, Google Cloud steps;
   - model roles;
   - a **Competition compliance** table (each rule in SPEC §2 → where the code enforces it);
   - open-source libraries + licenses;
   - Apache-2.0.
7. **Evidence pack** (`docs/evidence/`):
   - the "Prompt log" section of `docs/PROGRESS.md` complete;
   - the 2–3 key prompts as a PDF: SPEC v5 (short), `P2-ai-modules-python.md` (the AI prompt design), and one fix iteration (the 30 Oct browser test → P5 acceptance list), plus any `MANUAL` lines;
   - agent screenshots with the model name visible;
   - the smoke-test table;
   - Lighthouse reports;
   - a 60–90 second demo video script.
8. **`docs/PROGRESS.md`** final, with known limits stated honestly (e.g. the free CPU makes long media slow; data may reset when the Studio restarts; the Google OAuth consent screen is in test mode).

## Done when
- [ ] The Studio URL works for a fresh user in an incognito window, from register to the full loop.
- [ ] All checks above are green, with their outputs pasted in the report.
- [ ] A submission checklist for me: work title (identical to the Studio title), Studio link, project zip (no `.env`, no data, no `arsip/`), prompts PDF, screenshots folder. Each item ticked.
