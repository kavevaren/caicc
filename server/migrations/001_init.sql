-- Orvina 001_init.sql (SPEC §5) — applied in order at startup, recorded in schema_version.
-- Every object uses IF NOT EXISTS so the migration is safe to apply twice on an empty DB.
-- ISO-8601 UTC timestamps as TEXT. id INTEGER PRIMARY KEY unless noted.

-- users ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    lang TEXT NOT NULL DEFAULT 'id',
    theme TEXT NOT NULL DEFAULT 'system',
    reduce_motion INTEGER NOT NULL DEFAULT 0,
    notif_prefs_json TEXT,
    onboarding_done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

-- sessions (token_hash = sha256 of 32 random bytes; 30 days) --------------------
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);

-- stream tickets (single use, 60 s) ----------------------------------------------
CREATE TABLE IF NOT EXISTS stream_tickets (
    ticket_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);

-- subjects -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_subjects (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, subject_id)
);

-- documents (F1 summaries + F2 transcripts) ----------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('summary', 'transcript')),
    title TEXT NOT NULL,
    subject_id INTEGER REFERENCES subjects (id) ON DELETE SET NULL,
    source_files_json TEXT,
    content_md TEXT NOT NULL,
    extra_json TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_documents_user_kind ON documents (user_id, kind);
CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents (subject_id);

-- jobs (F1/F2 pipeline, thread pool) ----------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('summary', 'transcript')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'error')),
    stage TEXT NOT NULL DEFAULT 'queued',
    stages_json TEXT,
    result_document_id INTEGER REFERENCES documents (id) ON DELETE SET NULL,
    error_code TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs (user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);

-- events (F3) -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    location TEXT,
    description TEXT,
    reminder_minutes INTEGER,
    source TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'ai', 'google')),
    google_event_id TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_events_user_start ON events (user_id, start_at);

CREATE TABLE IF NOT EXISTS event_suggestions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    start_at TEXT NOT NULL,
    end_at TEXT,
    evidence TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'added', 'dismissed')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_suggestions_user_status ON event_suggestions (user_id, status);

-- Google OAuth ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS google_tokens (
    user_id INTEGER PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    enc_token TEXT NOT NULL,
    google_email TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- forum (F4) ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects (id) ON DELETE SET NULL,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 10 AND 150),
    body_md TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'answered')),
    best_answer_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_questions_user ON questions (user_id);
CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions (subject_id);
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions (status, created_at DESC);

CREATE TABLE IF NOT EXISTS question_tags (
    question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    tag TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_question_tags_tag ON question_tags (tag);

-- FTS5 full-text search, kept in sync by triggers (external content) -----------------
CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
    title,
    body_md,
    content='questions',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS questions_fts_ai AFTER INSERT ON questions BEGIN
    INSERT INTO questions_fts (rowid, title, body_md)
    VALUES (new.id, new.title, coalesce(new.body_md, ''));
END;

CREATE TRIGGER IF NOT EXISTS questions_fts_ad AFTER DELETE ON questions BEGIN
    INSERT INTO questions_fts (questions_fts, rowid, title, body_md)
    VALUES ('delete', old.id, old.title, coalesce(old.body_md, ''));
END;

CREATE TRIGGER IF NOT EXISTS questions_fts_au AFTER UPDATE ON questions BEGIN
    INSERT INTO questions_fts (questions_fts, rowid, title, body_md)
    VALUES ('delete', old.id, old.title, coalesce(old.body_md, ''));
    INSERT INTO questions_fts (rowid, title, body_md)
    VALUES (new.id, new.title, coalesce(new.body_md, ''));
END;

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    body_md TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_answers_question ON answers (question_id, created_at);
CREATE INDEX IF NOT EXISTS idx_answers_user ON answers (user_id);

CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY,
    owner_type TEXT NOT NULL CHECK (owner_type IN ('question', 'answer')),
    owner_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    mime TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_attachments_owner ON attachments (owner_type, owner_id);

CREATE TABLE IF NOT EXISTS votes (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    target_type TEXT NOT NULL CHECK (target_type IN ('answer')),
    target_id INTEGER NOT NULL,
    value INTEGER NOT NULL CHECK (value IN (1, -1)),
    UNIQUE (user_id, target_type, target_id)
);
CREATE INDEX IF NOT EXISTS idx_votes_target ON votes (target_type, target_id);

CREATE TABLE IF NOT EXISTS follows (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, question_id)
);

-- points (SPEC §11) --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS points_ledger (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    delta INTEGER NOT NULL,
    reason TEXT NOT NULL,
    ref_type TEXT,
    ref_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_points_user ON points_ledger (user_id, created_at);

CREATE TABLE IF NOT EXISTS hints_used (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, question_id)
);

-- notifications (SPEC §11) ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('event_soon', 'new_question', 'new_answer', 'best_answer', 'rank_change')),
    text_key TEXT NOT NULL,
    text_params_json TEXT,
    link TEXT,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_id, is_read, created_at DESC);

-- AI call tracing (never the prompt text, SPEC §5) -----------------------------------------------
CREATE TABLE IF NOT EXISTS ai_calls (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users (id) ON DELETE SET NULL,
    job_id TEXT REFERENCES jobs (id) ON DELETE SET NULL,
    feature TEXT NOT NULL,
    role TEXT NOT NULL,
    model TEXT NOT NULL,
    latency_ms INTEGER NOT NULL,
    retries INTEGER NOT NULL DEFAULT 0,
    ok INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_ai_calls_job ON ai_calls (job_id);

-- figures (F1, SPEC §10.5/§10.6) --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS figures (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    ref_no INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('extracted', 'chart')),
    source_label TEXT,
    category TEXT,
    caption TEXT NOT NULL,
    relevance REAL NOT NULL DEFAULT 0,
    included INTEGER NOT NULL DEFAULT 1,
    stored_path TEXT,
    width INTEGER,
    height INTEGER,
    chart_spec_json TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_figures_document ON figures (document_id);
