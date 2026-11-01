"""Idempotent demo seed (SPEC §12).

P1: stub — creates nothing. P6 fills in the demo data (5 users ending in
"(demo)", 3 subjects, 12 questions, 25 answers, votes, events) and keeps
the idempotency guarantee (safe to run on every startup of an empty DB).
"""
from __future__ import annotations

import logging

from server.store import db

log = logging.getLogger("orvina.seed")


def seed_if_empty() -> None:
    row = db.read_one("SELECT count(*) AS n FROM users")
    if row and row["n"] > 0:
        return
    # P6: insert demo data here (one transaction, explicit columns).
    log.info("database is empty; demo seed is a stub until P6")
