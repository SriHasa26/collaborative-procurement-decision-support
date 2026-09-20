"""
Phase 6G -- SQLite connection and schema management.
Phase 8F -- non-destructive schema evolution: adds the `user_id` column
needed for ownership filtering (backend/persistence/repository.py) to any
existing database that predates this phase, without dropping, recreating,
or deleting anything.

Infrastructure only: this module knows how to open a connection and make
sure the `procurement_runs` table exists. It contains no query that
inspects or interprets a run's content -- no WHERE clause here ever
decides BUY_TOGETHER, ABSTAIN, or eligibility; the table stores exactly
the already-computed ProcurementRunResult as an opaque JSON snapshot (see
backend/persistence/repository.py).

Uses Python's built-in sqlite3 module only -- no ORM, no SQLAlchemy. The
persistence model is one table with two JSON columns (Section 6 of this
phase's own spec); an ORM would be pure overhead for that shape.
"""

import sqlite3
from pathlib import Path
from typing import Union

# Kept out of data/raw/ and data/processed/ (research data, untouched by
# this phase) -- a separate application-data location, per this phase's
# own recommendation.
DEFAULT_DB_PATH = Path("data/app/procurement.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS procurement_runs (
    run_id                  TEXT PRIMARY KEY,
    user_id                  TEXT,
    created_at              TEXT NOT NULL,
    commodity                TEXT NOT NULL,
    run_status              TEXT NOT NULL,
    eligible_vendor_count   INTEGER NOT NULL,
    candidate_group_count   INTEGER NOT NULL,
    selected_group_count    INTEGER NOT NULL,
    input_json              TEXT NOT NULL,
    result_json             TEXT NOT NULL
)
"""

# `user_id` is nullable here for the identical reason Phase 8B's Postgres
# migration left it nullable: a legacy row saved before this phase (or
# before authentication existed at all) genuinely has no verified owner,
# and NULL is the honest representation of that -- not a placeholder to
# "fix" later by guessing an owner. `WHERE user_id = ?` never matches NULL
# in SQL, so such a row is simply never returned to any authenticated
# caller (repository.py, sqlite_repository.py) -- it is not deleted, and
# no owner is fabricated for it.


def _ensure_user_id_column(conn: sqlite3.Connection) -> None:
    """Adds the `user_id` column to a database file created by a
    pre-Phase-8F version of this project, without touching any existing
    row's data. SQLite has no `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
    syntax, so existence is checked explicitly via `PRAGMA table_info`
    first -- this is non-destructive (ADD COLUMN never drops or rewrites
    existing rows; the new column is NULL for all of them) and safe to
    call on every process start, exactly like the CREATE TABLE IF NOT
    EXISTS above."""
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(procurement_runs)").fetchall()}
    if "user_id" not in existing_columns:
        conn.execute("ALTER TABLE procurement_runs ADD COLUMN user_id TEXT")


def initialize_database(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> None:
    """Create the database's parent directory and the procurement_runs
    table if either is missing, and add the `user_id` column if the table
    already existed without one. Safe to call on every process start (and
    on every repository construction, see repository.py) -- it never
    drops, recreates, or deletes any existing table or row."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(_SCHEMA)
        _ensure_user_id_column(conn)
        conn.commit()
    finally:
        conn.close()


def get_connection(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """One short-lived connection per call -- opened and closed around a
    single repository operation (see repository.py), never held open
    across requests, so there is no shared mutable connection state to
    reason about under concurrent API requests."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
