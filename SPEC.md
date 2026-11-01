# Orvina: specification (v5, Python + React, built for ModelScope Studio)

> Single source of truth. Saved in the repo as `docs/SPEC.md`. Visual design: `docs/design/DESIGN.md`. Build plan: `prompts/P0` to `prompts/P6`.
> v5 (31 Oct 2026): one backend process instead of two. The Go gateway is dropped; **one Python FastAPI app** serves the React build, the public API, SQLite, jobs and the AI. Live captions (Presentasi langsung) are removed. Everything else (product, rules, data, pipelines, design) is unchanged from v4.
> If a prompt and this spec disagree, ask before writing code.

---

## §1. Product

**Orvina** is a collaborative study space for university students in Indonesia and China. Tagline: "Belajar bersama, paham lebih dalam" / "Learn together, understand deeper" / "一起学习，深入理解". One loop: **material → summary → questions → answers → schedule**.

| # | Feature | Core function |
|---|---|---|
| F1 | Ringkas Materi | PPTX, PDF, DOCX, TXT/MD, images, audio or video → summary with LaTeX, code, important figures and generated charts |
| F2 | Rekam & Transkrip | Record or upload audio/video (≤ 15 min), or import a transcript file (.srt/.vtt/.txt) → transcript → translations → meeting summary + action items |
| F3 | Jadwal | Google Calendar via OAuth, local fallback (.ics + template link), deadlines from summaries |
| F4 | Forum + Leaderboard | Q&A with LaTeX, code, images, documents, video; votes, best answer, points, leaderboard |

UI languages: Bahasa Indonesia (`id`, default), English (`en`), 中文 (`zh`).

---

## §2. Hard competition rules (any break = disqualification)

1. **Only these 4 LLMs**, via `https://api-inference.modelscope.ai/v1` (OpenAI-compatible): `zai-org/GLM-5.2`, `deepseek-ai/DeepSeek-V4-Pro-0813`, `stepfun-ai/Step-3.5-Flash`, `Qwen/Qwen3.8-27B`. No other model ID in any file, in any language.
2. **No proprietary AI service** from server or browser (OpenAI, Anthropic, Gemini, ElevenLabs …) and **no Web Speech API** (`SpeechRecognition`, `webkitSpeechRecognition`).
3. **Speech-to-text: faster-whisper on CPU, behind `ENABLE_TRANSCRIPTION`, pending written confirmation from the organizers.** The guide allows only the 4 models, and whisper is a model. Until the organizers confirm in writing, treat it as at risk:
   - every feature must still work with `ENABLE_TRANSCRIPTION=false`: F2 then offers only transcript-file import, and F1 reads video through keyframes only;
   - if the organizers say no, the submitted Studio runs with `ENABLE_TRANSCRIPTION=false` and `faster-whisper` is removed from `requirements.txt`.
4. **No training, no fine-tuning, no GPU.** Free CPU tier only.
5. **No secrets in code**: environment variables only (Studio Secrets / `.env`). Never logged, never in the web bundle.
6. **All code is written by the AI agent** (Claude Code or OpenCode configured with one of the 4 models). At most 30 hand-written lines, marked `MANUAL` in a comment; the agent never writes that marker.
7. **The Studio stays Public** and serves several judges at once.

Only `server/ai/llm.py` may call ModelScope. The browser never calls an LLM.

---

## §3. Architecture

### §3.1 Language per layer

| Layer | Language and stack | Why |
|---|---|---|
| Web UI | **TypeScript**, React 18, Vite, `motion` (Framer Motion 11), React Router 6, TanStack Query 5, i18next, react-markdown + KaTeX + highlight, react-pdf (attachment preview only), lucide-react, @fontsource (Outfit, Inter), CSS Modules | Typed components and API calls; the best animation tooling (springs, `layoutId` morphs, scroll-linked values) |
| Styles | **CSS** custom properties (`tokens.css`) + CSS Modules | Exact design tokens, theme switch with one attribute |
| Server (API, auth, jobs, AI) | **Python 3.10**: FastAPI + Uvicorn, stdlib `sqlite3`, `bcrypt`, `cryptography` (AES-GCM), `httpx` (Google OAuth + Calendar), `python-multipart`, `pydantic` v2, `openai` (HTTP client for ModelScope), faster-whisper, PyAV, pypdf, pypdfium2, python-pptx, python-docx, Pillow, imagehash, matplotlib, sympy, numpy | One process and one language for the whole backend: the simplest thing that runs on one free-CPU Studio container. All AI and document libraries are Python anyway |
| Data | **SQL**: SQLite (WAL, FTS5); numbered migration files in `server/migrations/` | One file, no DB server, full-text search for the forum |
| Contract | **OpenAPI 3.1 YAML** (`contracts/openapi.yaml`) | Source for FastAPI schemas and the generated TS types (`openapi-typescript`) |
| Packaging | **Dockerfile** (2 stages: Node build, Python runtime) | One image, one process on ModelScope Studio |

### §3.2 Runtime

```
Browser (React SPA, usually inside the Studio iframe)
   │  HTTPS JSON · SSE for job progress (polling fallback)
   ▼
server (Python, FastAPI, uvicorn --workers 1, 0.0.0.0:7860, the only port)
   ├─ serves web/dist (SPA fallback) and /api/*
   ├─ store/: SQLite (users, sessions, forum, events, points, notifications, jobs, documents)
   ├─ api/: routers per area, auth, rate limits, error JSON
   ├─ jobs/: thread pool (JOB_WORKERS = 2) for F1/F2, progress hub → SSE
   ├─ ai/: LLM client (4 models, roles, retries, JSON repair, call tracing),
   │       extraction, summarize, figures, charts, meeting, forum AI, whisper
   └─ domain/: points, notifications, Google Calendar, .ics
Disk: DATA_DIR (/data if writable, else /tmp/orvina): orvina.db, uploads/, figures/, models/
```

- **One process.** No supervisor, no internal port, no engine key. Startup: migrate → seed if empty → start listening. Whisper loads lazily in a background thread on the first F2/F1-video job (or at startup when `WHISPER_PRELOAD=true`), so the port opens within seconds.
- **SQLite access.** One connection per thread (`threading.local`), `PRAGMA journal_mode=WAL; foreign_keys=ON; busy_timeout=5000`. Every write goes through `store.db.write()`, which holds one process-wide lock, so there are no lock errors under load.
- **Blocking work** (AI calls, file parsing, whisper) never runs on the event loop: routes are plain `def` (FastAPI's threadpool) or jobs on the thread pool.
- **AI isolation.** Only `server/ai/` imports `openai`; only `server/ai/llm.py` creates a client. `ai/` never touches the database: it takes inputs, returns results plus an `ai_calls` list, and the caller stores them.

### §3.3 Request flows
- **CRUD** (auth, forum, events, points, notifications): browser → FastAPI → SQLite, < 100 ms.
- **AI inside CRUD** (similar questions, tags, moderation, AI hint): router → `ai/forum_ai.py`, timeout 30 s, then store.
- **Jobs** (F1 summary, F2 transcript): `POST /api/summaries` saves uploads and a `jobs` row, returns `{job_id}` in < 2 s → the thread pool runs the pipeline → each stage updates `jobs.stage` and is published to the progress hub → SSE pushes it to the browser → the result is stored as a document + figures + suggestions + `ai_calls`.

---

## §4. Repository layout

```
web/                         TypeScript
  src/app/                   router, providers, AppShell, ErrorBoundary
  src/components/ui/         Button, Card, Chip, StatStrip, Segmented, Tabs, Sheet, Toast, Skeleton,
                             Markdown, FileDrop, Avatar, EmptyState
  src/components/atom/       useOrbit, project, WeekAtom, DayAtom, WeekRing, AtomLoader, StageAtom
  src/pages/                 Login, Register, Onboarding, Dashboard, Summarize, DocumentView, Transcribe,
                             Schedule, Forum, Ask, QuestionView, Leaderboard, Library, Notifications, Profile
  src/lib/api.ts             typed client from contracts/openapi.yaml; relative URLs; Bearer; error → i18n key
  src/lib/api-types.ts       generated by openapi-typescript (never edited by hand)
  src/locales/               id.json, en.json, zh.json (identical keys)
  src/styles/                tokens.css, global.css
server/                      Python
  main.py                    FastAPI app: lifespan (migrate, seed), routers, SPA static, error handlers
  config.py                  environment variables (§4.1)
  api/                       deps.py (auth, rate limit), errors.py, one router per area (§6)
  store/                     db.py (connections, write lock, migrations), one module per table group
  migrations/                001_init.sql, 002_….sql
  jobs/                      runner.py (thread pool), hub.py (progress pub/sub), sse.py
  ai/                        llm.py, prompts.py, schemas.py, extract.py, media.py, transcribe.py,
                             summarize.py, figures.py, charts.py, meeting.py, forum_ai.py
  domain/                    points.py, notify.py, google_cal.py, ics.py, dashboard.py
  seed.py                    `python -m server.seed` (idempotent)
  tests/
  requirements.txt
contracts/openapi.yaml       public API (browser ↔ server)
scripts/                     smoke_test.py, compliance.py
e2e/                         Playwright tests and screenshots
assets/brand/                orvina-icon-light.svg (A), orvina-app-icon.svg (D)
docs/                        SPEC.md, design/DESIGN.md, design/dashboard-mockup.html, PROGRESS.md, evidence/
arsip/                       old code and prompts kept as history (never deployed)
Dockerfile  ms_deploy.json  .dockerignore  .env.example  .gitignore  Makefile  README.md
```

`Makefile` targets: `dev` (uvicorn --reload + Vite with a proxy to :7860), `test` (pytest, vitest), `lint` (ruff, eslint, tsc), `build`, `e2e`, `compliance`, `docker`.

### §4.1 Environment variables

| Name | Required | Default | Used for |
|---|---|---|---|
| `MODELSCOPE_TOKEN` | yes | — | `ai/llm.py` |
| `APP_SECRET_KEY` | yes | — | AES-GCM for Google tokens |
| `DATA_DIR` | no | `/data` if writable, else `/tmp/orvina` | DB, uploads, figures, models |
| `PORT` | no | `7860` | uvicorn |
| `PUBLIC_APP_URL` | no | — | OAuth redirect, "Buka di tab baru" |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | for F3 | — | Google Calendar |
| `ENABLE_TRANSCRIPTION` | no | `true` | whisper on/off (§2.3) |
| `WHISPER_MODEL` | no | `base` | whisper size |
| `WHISPER_PRELOAD` | no | `false` | load whisper at startup |
| `MAX_MEDIA_MINUTES` | no | `15` | media length limit |
| `MAX_UPLOAD_MB` | no | `200` | per-file limit (lowered if the Studio proxy accepts less, see §13) |
| `JOB_WORKERS` | no | `2` | concurrent F1/F2 jobs |

Missing Google variables → F3 runs in local mode and the UI explains why.

---

## §5. Data model (SQL, `server/migrations/`)

ISO-8601 UTC timestamps. `id INTEGER PRIMARY KEY` unless noted. Migrations are numbered `.sql` files, applied in order at startup and recorded in `schema_version`. `PRAGMA journal_mode=WAL; foreign_keys=ON; busy_timeout=5000`.

| Table | Columns |
|---|---|
| `users` | username UNIQUE, display_name, password_hash, lang, theme ('system'/'light'/'dark'), reduce_motion 0, notif_prefs_json, onboarding_done 0, created_at |
| `sessions` | token_hash TEXT PK (sha256 of 32 random bytes), user_id, created_at, expires_at (30 days) |
| `stream_tickets` | ticket_hash TEXT PK, user_id, expires_at (60 s), used 0 |
| `subjects` | name UNIQUE |
| `user_subjects` | user_id, subject_id (PK both) |
| `documents` | user_id, kind ('summary'/'transcript'), title, subject_id NULL, source_files_json, content_md, extra_json (segments, translations, decisions, action items, sources), created_at |
| `jobs` | id TEXT PK (uuid), user_id, kind, status ('queued'/'running'/'done'/'error'), stage, stages_json, result_document_id NULL, error_code NULL, created_at, updated_at |
| `events` | user_id, title, start_at, end_at, location, description, reminder_minutes, source ('manual'/'ai'/'google'), google_event_id NULL, created_at |
| `event_suggestions` | user_id, document_id, title, start_at, end_at NULL, evidence, status ('pending'/'added'/'dismissed') |
| `google_tokens` | user_id PK, enc_token, google_email, updated_at |
| `oauth_states` | state PK, user_id, created_at (10 min) |
| `questions` | user_id, subject_id, title, body_md, status ('open'/'answered'), best_answer_id NULL, created_at, updated_at, deleted 0 |
| `question_tags` | question_id, tag |
| `questions_fts` | FTS5(title, body_md), kept in sync by triggers |
| `answers` | question_id, user_id, body_md, created_at, updated_at, deleted 0 |
| `attachments` | owner_type ('question'/'answer'), owner_id, filename, stored_path, mime, size_bytes, created_at |
| `votes` | user_id, target_type, target_id, value (+1/−1), UNIQUE(user_id, target_type, target_id) |
| `follows` | user_id, question_id (PK both) |
| `points_ledger` | user_id, delta, reason, ref_type, ref_id, created_at |
| `hints_used` | user_id, question_id, count |
| `notifications` | user_id, kind, text_key, text_params_json, link, is_read 0, created_at |
| `ai_calls` | user_id NULL, job_id NULL, feature, role, model, latency_ms, retries, ok, created_at (never prompt text) |
| `figures` | document_id, ref_no, kind ('extracted'/'chart'), source_label, category, caption, relevance, included, stored_path, width, height, chart_spec_json NULL, created_at |

Uploads: `DATA_DIR/uploads/<uuid>.<ext>`, never the original name. Every INSERT names its columns explicitly (the 30 Oct test hit "11 values for 10 columns"). Empty database at startup → migrate, then seed demo data.

---

## §6. Public API (`contracts/openapi.yaml`, served by FastAPI)

**Conventions.**
- JSON, except uploads (multipart) and downloads.
- Errors: `{"error":{"code":"…","message_key":"errors.<code>"}}` with a proper status. Global exception handlers guarantee no stack trace reaches a user; details go to the log.
- **Auth: Bearer token** in `Authorization`. The Studio embeds the app in a cross-site iframe where cookies are unreliable, so the token lives in `localStorage`. SSE uses `POST /api/stream-ticket` → 60-second single-use `?ticket=`.
- Lists paginate (20). Writes are validated by pydantic models matching the OpenAPI schema.
- Rate limits per user (in memory): AI endpoints 20/min, uploads 10/min.
- `ai_unavailable` → 502 · `modelscope_token_invalid` → 503 (from the cached health check).

| Area | Endpoints |
|---|---|
| Health | `GET /api/health` → `{server:"ok", modelscope:"ok"\|"invalid_token"\|"unreachable", whisper:"ready"\|"loading"\|"idle"\|"disabled", version}` (ModelScope result cached 5 min) |
| Auth | `POST /api/auth/register` `{username, display_name, password, lang, accept_terms}` → `{token, user}`; codes `username_taken`, `terms_required`, `weak_password`, `invalid_username` · `POST /api/auth/login` (generic `invalid_credentials`) · `POST /api/auth/logout` · `POST /api/stream-ticket` |
| Me | `GET /api/me` (user, settings, points, rank, unread, onboarding_done) · `PATCH /api/me` · `POST /api/me/password` · `POST /api/me/onboarding` `{lang, subject_ids, new_subjects, done}` |
| Subjects | `GET /api/subjects` · `POST /api/subjects` |
| Dashboard | `GET /api/dashboard` → `{week[7]{date, events[]}, next_event, stats, points_ring, questions_for_you, reminders, top5, me_row, recent}` (one call, real data) |
| Jobs | `GET /api/jobs/{id}` (also the polling fallback) · `GET /api/jobs/{id}/stream?ticket=` (SSE events `stage`, `done`, `error`, comment heartbeat every 15 s) |
| F1 | `POST /api/summaries` (multipart files + options) → `{job_id}` · `GET /api/documents?kind&q&subject&page` · `GET/PATCH/DELETE /api/documents/{id}` · `PATCH /api/documents/{id}/figures/{ref}` `{included}` · `GET /api/documents/{id}/export?format=md\|html` · `GET /api/figures/{id}.png` |
| F2 | `POST /api/transcripts` (multipart: media, recorded blob, or transcript file .srt/.vtt/.txt + options) → `{job_id}` |
| F3 | `GET /api/events?from&to` · `POST /api/events` · `PATCH/DELETE /api/events/{id}` · `GET /api/events/{id}.ics` · `GET /api/suggestions` · `POST /api/suggestions/{id}/accept\|dismiss` · `GET /api/google/connect` → `{url}` · `GET /api/google/callback` (HTML "Google Calendar terhubung, tab ini boleh ditutup") · `DELETE /api/google` |
| F4 | `GET/POST /api/questions` · `POST /api/questions/similar` · `POST /api/questions/tags` · `GET/PATCH/DELETE /api/questions/{id}` · `POST /api/questions/{id}/answers` · `PATCH/DELETE /api/answers/{id}` · `POST /api/votes` · `POST /api/questions/{id}/best` · `POST /api/questions/{id}/follow` · `POST /api/questions/{id}/hint` |
| Points | `GET /api/leaderboard?window=week\|month\|all&subject` |
| Notifications | `GET /api/notifications?unread=1` · `POST /api/notifications/{id}/read` · `POST /api/notifications/read-all` |
| Files | `GET /api/files/{attachment_id}` (visibility checked) |

---

## §7. AI module interface (`server/ai/`, in-process)

There is no internal HTTP API. The jobs and routers call these functions directly. Each returns its result plus `ai_calls: [{feature, role, model, latency_ms, retries, ok}]` for the caller to store, and raises `AIError(code, params)` on failure.

| Function | Input | Output |
|---|---|---|
| `health()` | — | `{modelscope, whisper}` |
| `summarize(job_id, files, options, on_stage)` | files `[{path, name, mime}]`, options `{style, lang, detail, extra, include_figures, generate_charts}` | `{content_md, figures:[{ref_no, kind, source_label, category, caption, relevance, included, path, width, height, chart_spec}], sources:[{label, text}], deadlines:[{title, start_at, end_at, evidence}], ai_calls}` |
| `transcribe(job_id, path, options, on_stage)` | options `{source_lang, targets[], summary}`; `path` is media or a transcript file | stages `probe`, `transcribe` (or `parse` for a transcript file), `translate`, `summarize` → `{language, segments:[{start,end,text}], translations:{lang:[…]}, meeting:{summary_md, decisions[], action_items[{who, what, due}]}, ai_calls}` |
| `forum_similar(title, body, candidates)` | candidates = FTS5 top 10 `[{id, title, excerpt}]` | `{ids[≤3]}` |
| `forum_tags(title, body)` | — | `{tags[≤5]}` |
| `forum_moderate(text)` | — | `{allowed, reason_key}` (fail open on API error) |
| `forum_hint(question_md, answers_md, lang)` | — | `{hint_md}` |

`on_stage(name)` is called when each stage starts; the job runner publishes it to the progress hub. The duration check (`MAX_MEDIA_MINUTES`) happens in `probe` and raises `AIError("media_too_long", {"minutes": …})`. With `ENABLE_TRANSCRIPTION=false`, media input to `transcribe` raises `AIError("transcription_disabled")` and the UI offers transcript import instead.

---

## §8. Pages (functional content; layout and motion in DESIGN.md)

Navigation: **Dashboard, Ringkas Materi, Rekam & Transkrip, Jadwal, Forum, Leaderboard, Perpustakaan, Notifikasi, Profil & Pengaturan**. Logged-out users see only Masuk / Daftar.

- **§8.1 Masuk / Daftar / Onboarding.**
  - Username: 3–20 characters `[A-Za-z0-9_]`, unique. Display name. Password ≥ 8 characters + confirm. Language. Terms checkbox (error `terms_required`: "Setujui syarat dan ketentuan untuk mendaftar").
  - Errors appear under their field. A failed login never reveals whether the username exists.
  - After register: a **3-step onboarding, once**: language → subjects to follow (pick + add) → connect Google (skippable).
- **§8.2 Dashboard.**
  - Header: greeting, date, language switch, bell, theme toggle.
  - Hero "Minggu ini" with the week atom.
  - Stat strip: summaries, transcripts, my unanswered questions, points + rank.
  - Quick actions: "Ringkas materi baru" (the only primary button), "Rekam kelas", "Ajukan pertanyaan".
  - Two columns: left "7 hari ke depan" and "Pertanyaan untuk kamu"; right "Pengingat", "Top 5 minggu ini" (with a "Kamu" row), "Aktivitas terakhir".
- **§8.3 Ringkas Materi.**
  - Files: pdf, pptx, docx, txt, md, png, jpg, jpeg, mp4, mov, webm, mp3, wav, m4a; ≤ 10 files, ≤ `MAX_UPLOAD_MB` each.
  - Options:
    - title (from the first filename);
    - subject (select + add);
    - style: Ringkas 1 halaman · Catatan terstruktur · Poin kunci + rumus + kode · Latihan tanya jawab;
    - output language id/en/zh;
    - detail: Singkat · Standar · Detail;
    - extra instructions ≤ 500 characters;
    - include images (on); generate charts (on).
  - Result:
    - the stage atom during processing;
    - tabs Ringkasan · Gambar (include toggles re-render with no model call) · Sumber · Ekspor (.md zip, .html, deadlines → Jadwal, ask in Forum);
    - "Di balik layar" showing role, model, latency, retries.
- **§8.4 Rekam & Transkrip.**
  - Page title and subtitle.
  - Modes: Rekam · Unggah. Unggah accepts media or a transcript file (.srt, .vtt, .txt). With transcription disabled, Rekam is hidden and Unggah accepts transcript files only, with one line explaining why.
  - Rekam needs the microphone. Inside the Studio iframe, if `getUserMedia` is blocked, show "Buka di tab baru" (`PUBLIC_APP_URL/transcribe`).
  - Fields: session title, source language (Auto/id/en/zh), translate to (multi), summary on.
  - Media over the limit is refused with its real duration.
  - Result tabs: Transkrip (`[mm:ss]`, search) · Terjemahan · Ringkasan · Keputusan · Action items (dated items get "Tambah ke Jadwal").
  - Downloads .txt, .srt, .md.
- **§8.5 Jadwal.**
  - Google card: Connect opens a **new tab**; when connected, shows the email + Disconnect.
  - 30 days grouped by day, with the day atom.
  - New event: title, date, start, end (**default start + 1 h; end ≤ start rejected**), location, description, reminder (10 min / 1 h / 1 day).
  - Suggestions with Terima / Abaikan.
  - Every event has the template link + .ics.
- **§8.6 Forum.** Routes `/forum`, `/forum/ask`, `/forum/q/:id`.
  - List:
    - FTS5 search;
    - filters status (Semua · Belum terjawab · Terjawab · Diikuti), sort (Terbaru · Vote terbanyak · Tanpa jawaban), subject;
    - rows: title, 160-character excerpt, tags, author, time, answers, score, attachment icon, "Terjawab" chip.
  - Empty list: no "Buka" button; the CTA is "Ajukan pertanyaan".
  - Ask:
    - title 10–150 characters (client and server);
    - similar questions shown as links;
    - body ≤ 10,000 characters with write/preview;
    - subject (required), tags (free + ≤ 5 AI suggestions), attachments ≤ 10;
    - submit → moderation → publish → +2 points → notify followers.
  - Detail:
    - attachments: images inline, PDF preview, video player, other files as links;
    - votes (no self-votes), follow, owner edit/delete;
    - answers: best first, then score, then time;
    - "Tandai jawaban terbaik";
    - answer form with preview, attachments, "Minta petunjuk AI" (box labelled "Petunjuk AI, bukan jawaban", max 3 per user per question, never posted).
- **§8.7 Leaderboard.**
  - Tabs: Minggu ini · Bulan ini · Sepanjang waktu.
  - Subject filter, top-3 podium.
  - Rows: rank, name, points, answers, best answers.
  - Sticky "Kamu" row and "Cara dapat poin".
- **§8.8 Perpustakaan · Notifikasi · Profil.**
  - Perpustakaan: search, filters, open/rename/download/delete/ask.
  - Notifikasi: the newest 100, unread filter, "Tandai semua dibaca".
  - Profil:
    - display name, language, theme, "Kurangi animasi", followed subjects;
    - notification preferences with translated labels;
    - Google card;
    - change password;
    - stats and points history.
- **§8.9 Shared rules.**
  - One primary button per page. No emoji. Sentence case. Indonesian date/time formats.
  - Markdown + KaTeX + highlighted code; **raw HTML in user content is never rendered**.
  - Every error is translated with "Coba lagi".
  - Usable at 400 px. WCAG AA in both themes. Reduced motion respected.

---

## §9. Integrations

- **§9.1 LLM client (`server/ai/llm.py`).**
  - `chat(role, messages, *, json_schema=None, images=None, feature)`.
  - Role → model:

    | Role | Model |
    |---|---|
    | VISION | `Qwen/Qwen3.8-27B` |
    | FAST | `stepfun-ai/Step-3.5-Flash` |
    | REASON | `deepseek-ai/DeepSeek-V4-Pro-0813` |
    | CHECK | `zai-org/GLM-5.2` |

  - Rejects any model outside §2.
  - Timeout 120 s; backoff on 429/5xx/timeout (max 2 retries); 401 raises `ModelScopeAuthError` immediately.
  - Images only for VISION (≤ 1600 px, base64).
  - JSON: extract → pydantic → one repair retry.
  - Each call is appended to the request's `ai_calls`.
- **§9.2 Whisper (`server/ai/transcribe.py`, only when `ENABLE_TRANSCRIPTION=true`).**
  - `WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")`, loaded once, lazily, one global lock.
  - VAD on, `beam_size=1`.
  - Model source order: `DATA_DIR/models` or baked into the image at `/opt/models` → Hugging Face → ModelScope hub.
  - Transcript files: `.srt`/`.vtt` parsed into timed segments; `.txt` split into sentences with no timestamps.
- **§9.3 Google Calendar (`server/domain/google_cal.py`, `httpx`).**
  - Scopes `openid`, `userinfo.email`, `calendar.events`.
  - `connect` creates a `state` → the browser opens the URL in a new tab → `callback` exchanges the code and stores the token encrypted (AES-GCM, key from `APP_SECRET_KEY`) → returns the HTML page.
  - Auto refresh; `invalid_grant` → disconnected + notification.
  - Redirect URI `PUBLIC_APP_URL/api/google/callback`.
- **§9.4 Local mode.** Events live in `events`, each with the template link (`https://calendar.google.com/calendar/render?action=TEMPLATE&text=…&dates=…&details=…&location=…`) and an RFC 5545 `.ics`.

---

## §10. AI pipelines (`server/ai/`; prompts in `prompts.py`, English, `PROMPT_VERSION`, explicit `Respond only in {language}.`, 1–2 few-shot examples for strict formats)

- **§10.1 Summarize.** Stages: `extract` → `figures` → `chunk` → `map` → `reduce` → `format_check` → `deadlines`.
  1. **Extract**:
     - PDF text via pypdf; a page with < 80 characters → render at 150 dpi → VISION ("all text, formulas as LaTeX, code as code").
     - PPTX: text + notes; a slide with < 30 characters and pictures → largest picture → VISION.
     - DOCX: paragraphs + tables. TXT/MD: as is. Images: VISION.
     - Video: keyframes every 30 s (≤ 20) → VISION; plus audio → whisper when transcription is enabled; merged by time.
  2. **Figures**: see §10.6.
  3. **Chunk**: ~6,000 characters on page/slide/heading boundaries, keeping source labels.
  4. **Map** (FAST): per-chunk notes in the output language; LaTeX, fenced code; never invent content.
  5. **Reduce** (REASON): the chosen style, with the selected figures (ref_no, caption, category, source).
     - It may place `[[img:N]]` once per listed figure and `[[chart:N]]` + ≤ 6 specs between `<<<CHARTS` and `CHARTS>>>`.
     - Sections: Title, TL;DR (3 bullets), content, key formulas (`$$`), code, glossary, dates/deadlines, source map.
  6. **Format check** (Python): balanced `$`/`$$`, closed fences, no raw HTML. If broken → CHECK repairs the format only; a second failure is returned with a warning flag.
  7. **Deadlines** (CHECK): JSON `[{title, start_at, end_at|null, evidence}]`; no year → next occurrence; unresolvable dates are dropped.
- **§10.2 Meeting.** Segments (from whisper or a transcript file) → FAST translation in batches (same count and timestamps) → REASON `{summary_md, decisions[], action_items[{who|null, what, due|null}]}` from what was said only → dated items become suggestions.
- **§10.3 Language.** Output is always the user's chosen language.
- **§10.4 Forum AI.**
  - Similar: FAST picks ≤ 3 of the FTS5 top 10.
  - Tags: FAST, ≤ 5 lowercase tags.
  - Moderation: CHECK → `{allowed, reason_key: spam|abusive|off_topic|ok}`, failing open.
  - Hint: REASON gives one or two hints or a guiding question, **never the final answer**.
- **§10.5 Figures.**
  - Candidates (no AI): PDF images or scanned pages, PPTX pictures, DOCX images, keyframes, standalone images.
  - Filter (no AI): drop < 200×120 px or < 8 KB, aspect > 6:1, near-duplicates (imagehash Hamming ≤ 6), hashes on ≥ 3 pages (logos); keep ≤ 40.
  - Caption and score with VISION `FIGURE_CAPTION` `{category, caption, relevance}`, within the 30-call VISION cap.
  - Select relevance ≥ 0.6, not decorative, ≤ 12, in source order.
- **§10.6 Charts.**
  - Never an image model, never executing LLM-written code. REASON writes a JSON `ChartSpec`: `ref_no, title, x_label, y_label, caption, type: function|scatter|bar|line`. Functions: 1–4 `{expr, label}` in `x`, `x_range`, optional `marks`. Data: ≤ 200 points, only numbers from the source.
  - `sympy.parse_expr` on a whitelist (`x`, numbers, `+ - * / **`, `sin cos tan exp log sqrt abs pi E`), no attributes, ≤ 200 characters; `lambdify` with numpy on 400 points; mask non-finite values.
  - matplotlib Agg, 1200×750 PNG, CJK font for `zh`. ≤ 6 per summary. Invalid specs are dropped with their markers.
- **§10.7 Exports** (`server/domain/`).
  - HTML: base64 images + `<figcaption>`, KaTeX/highlight from a CDN inside the file.
  - Markdown: zip with `summary.md` + `images/`.

---

## §11. Points, limits, notifications

- **Points.**

  | Action | Points |
  |---|---|
  | Ask | +2 |
  | Answer | +5 |
  | Upvote on an answer | +2 (reversed on removal) |
  | Downvote on an answer | −1 (reversed on removal) |
  | Best answer | +15 (moves if the best answer changes) |
  | Asker marks a best answer | +2 (once per question) |

  Deleting a post reverses its points. "This week" starts Monday 00:00 Asia/Jakarta.
- **Limits.**
  - Files: `MAX_UPLOAD_MB` per file, 10 files per upload, 15 min of media, 10,000 characters per post.
  - AI: 3 hints per user per question, 30 VISION calls per job, 40 figure candidates / 12 figures / 6 charts per summary.
  - Concurrency: `JOB_WORKERS` (2) jobs; more are queued, never refused.
- **Notifications** (created when the action happens, no scheduler; per-kind user preferences):

  | Kind | Label |
  |---|---|
  | `event_soon` | Acara segera dimulai (on app open, event within 24 h, once) |
  | `new_question` | Pertanyaan baru di mata kuliahmu |
  | `new_answer` | Jawaban baru |
  | `best_answer` | Jawabanmu jadi yang terbaik |
  | `rank_change` | Perubahan peringkat (entered/left the weekly top 10) |

---

## §12. Quality bar

- **Python** (`pytest`, `ruff`), fake LLM:
  - auth and sessions, stream tickets;
  - every router (status, error JSON, validation) via `TestClient`;
  - points incl. reversals, leaderboard windows, vote uniqueness and no self-votes;
  - events INSERT column match, .ics and template link, OAuth state;
  - job runner with a fake pipeline (stages, error mapping, queueing beyond `JOB_WORKERS`);
  - SQLite: migrations run twice; 20 concurrent writers without "database is locked";
  - LLM client (retry, 401, JSON repair, model guard);
  - extractors on generated files, figure filter and selection, chart spec validation (rejects `__import__('os')`, attribute access);
  - format check, deadline parsing, .srt/.vtt/.txt transcript parsing;
  - `ENABLE_TRANSCRIPTION=false`: the app starts, health says `disabled`, transcript import works.
- **TypeScript** (Vitest, ESLint with `i18next/no-literal-string`, `tsc --noEmit`): locale key parity, atom geometry (`project`), API error mapping, SSE → polling fallback, components with Testing Library.
- **Contract**: FastAPI routes are tested against `contracts/openapi.yaml` (schemathesis), and `api-types.ts` is regenerated from it.
- **E2E** (Playwright):
  - one full loop: register → onboarding → summarize → ask → answer from user 2 → best answer → deadline in Jadwal;
  - screenshots of every page in light, dark and 400 px.
- **Compliance** (`make compliance`, scans `.py .ts .tsx .json .yaml .md`). Fails on:
  - a non-allowed model ID, or `openai` imported outside `server/ai/`;
  - a forbidden AI domain or `SpeechRecognition`;
  - a token-like string;
  - emoji in UI strings;
  - more than 30 `MANUAL` lines.
- **Smoke test** (`scripts/smoke_test.py`, real token): 4 models (OK/FAIL + latency), VISION on a generated "∫ x dx = x²/2 + C" image, whisper load + 3 s silent WAV (skipped when disabled).
- **Seed** (`python -m server.seed`, idempotent, also run on an empty DB at startup): 5 demo users ending in "(demo)", 3 subjects, 12 questions with LaTeX and code, 25 answers, votes, best answers, events this week.
- **Performance**: Lighthouse on the Dashboard: Performance ≥ 85, Accessibility ≥ 95. 60 fps for the atom on a mid-range laptop. p95 < 300 ms for dashboard + forum list with 20 concurrent users on the free CPU.
- **Docs**:
  - README: setup, Docker, environment variables, Studio Secrets, Google Cloud steps, model roles, a **compliance map** (§2 → code), licenses (Apache-2.0).
  - `docs/PROGRESS.md` updated after every task and phase (competition evidence).

---

## §13. Deployment (ModelScope Studio, Docker, free CPU)

**`ms_deploy.json`:** `{"sdk_type":"docker","port":7860,"resource_configuration":"<the free CPU option exactly as the Studio deployment page names it>"}`. P0 reads that name from the Studio UI; never pick a paid, GPU or xGPU option.

**`Dockerfile` (2 stages):**
1. `node:20-slim` → `npm ci` (lockfile committed) → `npm run build` → `web/dist`. Vite `base: "./"`.
2. `python:3.10-slim` → `apt-get install -y --no-install-recommends fonts-noto-cjk` (zh charts) → `pip install --no-cache-dir -r server/requirements.txt` (pinned versions) → copy `server/`, `contracts/` and `web/dist` → optional whisper pre-download into `/opt/models` (`|| true`, so a slow build network never breaks the build) → `EXPOSE 7860` → `CMD uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1 --proxy-headers --forwarded-allow-ips "*"`.

**Rules that make it work on the Studio:**
- **One process, one worker, `0.0.0.0:7860`.** The port in `ms_deploy.json`, `EXPOSE` and uvicorn must match.
- **Fast start.** The port opens within seconds; whisper loads lazily; the ModelScope health check runs in the background and is cached.
- **Secrets** (`MODELSCOPE_TOKEN`, `APP_SECRET_KEY`, `PUBLIC_APP_URL`, Google vars) are set in the Studio's Variables / Secrets panel, never in files.
- **Disk may be wiped on restart.** `DATA_DIR=/data` if writable, else `/tmp/orvina`; an empty DB is migrated and seeded automatically, so the demo always works. State this limit in the README.
- **Iframe.** The Studio shows the app in a cross-site iframe:
  - relative URLs everywhere (assets and `/api`), so it works at a domain root or under a path;
  - Bearer token in `localStorage`, no cookies;
  - microphone and Google connect: if blocked, "Buka di tab baru" with `PUBLIC_APP_URL`.
- **Proxy.** SSE responses send `Cache-Control: no-cache` and `X-Accel-Buffering: no`, plus a heartbeat every 15 s. If the browser gets no SSE event within 10 s, it switches to polling `GET /api/jobs/{id}` every 2 s. P0 checks whether the Studio proxy buffers SSE.
- **Uploads.** P0 measures the largest upload the Studio proxy accepts. If it is under 200 MB, set `MAX_UPLOAD_MB` to match and show it in the drop zone.
- **RAM.** Report peak RAM idle, during a summary job, and with whisper loaded; if it is close to the free tier's limit, set `WHISPER_MODEL=tiny` or `ENABLE_TRANSCRIPTION=false`.
- **`.dockerignore`** excludes `.env`, `docs/`, `prompts/`, `arsip/`, `e2e/`, `scripts/`, `web/node_modules/`, data and caches.

**Fallback if the Studio rejects Docker:** the Gradio SDK with an `app.py` that serves the same FastAPI app on port 7860 (`uvicorn.run(server.main.app, host="0.0.0.0", port=7860)`), with `web/dist` built locally and uploaded with the files. Test it only if Docker fails. Last resort: the old Streamlit app in `CAICC #2`.
