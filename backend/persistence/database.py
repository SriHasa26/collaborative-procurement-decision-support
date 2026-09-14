"""
Phase 6G -- SQLite connection and schema management.

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


def initialize_database(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> None:
    """Create the database's parent directory and the procurement_runs
    table if either is missing. `CREATE TABLE IF NOT EXISTS` makes this
    safe to call on every process start (and on every repository
    construction, see repository.py) -- it never drops or resets existing
    data."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(_SCHEMA)
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
