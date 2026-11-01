"""SQLite access (SPEC §3.2, §5).

- One connection per thread (threading.local); PRAGMA journal_mode=WAL,
  foreign_keys=ON, busy_timeout=5000.
- Every write goes through write(), which holds one process-wide lock, so
  there are no lock errors under load.
- Migrations: numbered .sql files in server/migrations/, applied in order at
  startup and recorded in schema_version.
"""
from __future__ import annotations

import logging
import re
import sqlite3
import threading
from pathlib import Path

from server.config import settings

log = logging.getLogger("orvina.store")

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
DB_PATH = settings.data_dir / "orvina.db"

_local = threading.local()
_write_lock = threading.RLock()


def get_conn() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        _local.conn = conn
    return conn


def read(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return get_conn().execute(sql, params).fetchall()


def read_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return get_conn().execute(sql, params).fetchone()


def write(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """The only way to write. Holds the process-wide lock and commits."""
    with _write_lock:
        conn = get_conn()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur


def run_migrations() -> None:
    """Apply every unapplied migration, in filename order (SPEC §5)."""
    with _write_lock:
        conn = get_conn()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            " version INTEGER PRIMARY KEY,"
            " applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')))"
        )
        conn.commit()
        applied = {r["version"] for r in conn.execute("SELECT version FROM schema_version")}
        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for f in files:
            m = re.match(r"^(\d+)_", f.name)
            if not m:
                continue
            version = int(m.group(1))
            if version in applied:
                continue
            log.info("applying migration %s", f.name)
            conn.executescript(f.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()
        log.info("migrations up to date (%d files)", len(files))
