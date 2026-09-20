"""
Phase 6G -- SQLite-backed procurement-run persistence.
Phase 8B -- extracted from repository.py (which is now the shared
interface + value types only, backend/persistence/repository.py) and
renamed `ProcurementRunRepository` -> `SQLiteProcurementRunRepository`,
so it can sit alongside `supabase_repository.SupabaseProcurementRunRepository`
as one of two interchangeable implementations of the same
`ProcurementRunRepository` interface. Behavior is UNCHANGED from Phase 6G/6G:
same schema, same queries, same semantics -- this is a pure extract-and-rename,
not a rewrite. Existing SQLite regression tests continue to exercise this
exact code, just via an updated import path.
Phase 8F -- every method now takes `user_id` (the caller's verified
identity) as its first parameter and enforces ownership directly inside
its SQL: INSERT writes it, and every SELECT includes `user_id = ?` in its
WHERE clause -- never fetch-then-check-in-Python. A legacy row with a NULL
`user_id` (see database.py) matches no real `user_id` filter, so it is
simply never returned to any authenticated caller.

Responsible ONLY for reading and writing procurement_runs rows. Contains
no validation, eligibility, geographic, group-formation, or decision
logic -- it stores the ProcurementRunInput/ProcurementRunResult that
Phase 6E's ProcurementRunService already computed, as an opaque JSON
snapshot, and returns exactly what it stored. No query here ever branches
on decision content.

SERIALIZATION REUSE: input/result are converted to JSON via
backend.api.serialization.to_json_safe -- the same generic Enum/
dataclass/tuple/set -> JSON-safe converter Phase 6F already built and
tested for the HTTP response boundary. Reusing it here (rather than
writing a second converter) means there is exactly one place in the
project that knows how to turn these contracts into JSON, matching this
phase's own "do not duplicate serialization logic" instruction. This
creates a persistence -> api import, which is the reverse of the usual
web-layering direction; it is safe here because
backend/api/serialization.py has no FastAPI/HTTP-specific code at all
(pure dataclass/Enum walking) and this project's `backend/api/` package
does not import anything from `backend/persistence/` back -- there is no
cycle. See reports/phase6g_database_persistence.md Section 6 for the
original reasoning (unchanged by this phase's file split).
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from backend.api.serialization import to_json_safe
from backend.models.run_contracts import ProcurementRunInput, ProcurementRunResult
from backend.persistence.database import DEFAULT_DB_PATH, get_connection, initialize_database
from backend.persistence.repository import RunSummary, StoredRun


class SQLiteProcurementRunRepository:
    """The only component in this project allowed to open a SQLite
    connection for procurement runs. All queries are parameterized (`?`
    placeholders) -- no SQL is ever built via string interpolation of a
    caller-supplied value. Local-dev/offline-first behavior: creates the
    database file and table automatically if missing (via
    `initialize_database`), so a fresh checkout works with zero manual
    setup -- deliberately different from `SupabaseProcurementRunRepository`,
    whose schema is managed exclusively via a version-controlled migration
    (see supabase/migrations/), never created implicitly."""

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        self._db_path = db_path
        initialize_database(self._db_path)  # idempotent; safe on every construction

    def save_run(self, user_id: str, run_input: ProcurementRunInput, run_result: ProcurementRunResult) -> str:
        """Persist one already-computed run, owned by `user_id`. Never
        recomputes, never mutates run_input/run_result -- to_json_safe
        reads them, it does not modify them."""
        run_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        input_json = json.dumps(to_json_safe(run_input))
        result_json = json.dumps(to_json_safe(run_result))

        conn = get_connection(self._db_path)
        try:
            conn.execute(
                """
                INSERT INTO procurement_runs (
                    run_id, user_id, created_at, commodity, run_status,
                    eligible_vendor_count, candidate_group_count, selected_group_count,
                    input_json, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, user_id, created_at, run_result.commodity_id, run_result.run_status,
                    run_result.eligible_vendor_count, run_result.candidate_group_count,
                    run_result.selected_group_count, input_json, result_json,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return run_id

    def get_run(self, user_id: str, run_id: str) -> Optional[StoredRun]:
        """Returns the stored run, but ONLY if it is owned by `user_id` --
        None otherwise, identically to a genuinely nonexistent run_id.
        Ownership is enforced directly in the WHERE clause, not by
        fetching the row first and checking its owner in Python. Never
        lets a raw sqlite3.Error escape for a simple missing-row case."""
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                "SELECT run_id, created_at, commodity, run_status, input_json, result_json "
                "FROM procurement_runs WHERE run_id = ? AND user_id = ?",
                (run_id, user_id),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None

        return StoredRun(
            run_id=row["run_id"],
            created_at=row["created_at"],
            commodity=row["commodity"],
            run_status=row["run_status"],
            input=json.loads(row["input_json"]),
            result=json.loads(row["result_json"]),
        )

    def list_runs(self, user_id: str, limit: Optional[int] = None) -> List[RunSummary]:
        """Newest first (created_at descending, run_id descending as a
        deterministic tie-break for runs saved within the same
        microsecond), filtered to runs owned by `user_id` only. Metadata
        columns only -- never input_json/result_json."""
        query = (
            "SELECT run_id, created_at, commodity, run_status FROM procurement_runs "
            "WHERE user_id = ? ORDER BY created_at DESC, run_id DESC"
        )
        params: tuple = (user_id,)
        if limit is not None:
            query += " LIMIT ?"
            params = (user_id, limit)

        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()

        return [
            RunSummary(run_id=r["run_id"], created_at=r["created_at"], commodity=r["commodity"], run_status=r["run_status"])
            for r in rows
        ]
