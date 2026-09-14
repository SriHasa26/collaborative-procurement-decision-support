"""
Phase 6G -- procurement-run persistence repository.

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
explicit reasoning.
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


@dataclass(frozen=True)
class RunSummary:
    """Lightweight run-history row -- metadata only, no input/result JSON
    (Phase 6G's own "keep run-history responses lightweight" instruction)."""
    run_id: str
    created_at: str
    commodity: str
    run_status: str


@dataclass(frozen=True)
class StoredRun:
    """One fully-retrieved run: metadata plus the original input and
    complete result, exactly as they were saved -- `input`/`result` are
    already-parsed JSON-safe Python structures (dict/list/str/...), not
    reconstructed dataclasses and not re-derived in any way."""
    run_id: str
    created_at: str
    commodity: str
    run_status: str
    input: dict
    result: dict


class ProcurementRunRepository:
    """The only component in this project allowed to open a SQL
    connection for procurement runs. All queries are parameterized (`?`
    placeholders) -- no SQL is ever built via string interpolation of a
    caller-supplied value."""

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        self._db_path = db_path
        initialize_database(self._db_path)  # idempotent; safe on every construction

    def save_run(self, run_input: ProcurementRunInput, run_result: ProcurementRunResult) -> str:
        """Persist one already-computed run. Never recomputes, never
        mutates run_input/run_result -- to_json_safe reads them, it does
        not modify them."""
        run_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        input_json = json.dumps(to_json_safe(run_input))
        result_json = json.dumps(to_json_safe(run_result))

        conn = get_connection(self._db_path)
        try:
            conn.execute(
                """
                INSERT INTO procurement_runs (
                    run_id, created_at, commodity, run_status,
                    eligible_vendor_count, candidate_group_count, selected_group_count,
                    input_json, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, created_at, run_result.commodity_id, run_result.run_status,
                    run_result.eligible_vendor_count, run_result.candidate_group_count,
                    run_result.selected_group_count, input_json, result_json,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return run_id

    def get_run(self, run_id: str) -> Optional[StoredRun]:
        """Returns the stored run, or None -- a clear, typed,
        repository-level "not found" signal. Never lets a raw
        sqlite3.Error escape for a simple missing-row case."""
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                "SELECT run_id, created_at, commodity, run_status, input_json, result_json "
                "FROM procurement_runs WHERE run_id = ?",
                (run_id,),
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

    def list_runs(self, limit: Optional[int] = None) -> List[RunSummary]:
        """Newest first (created_at descending, run_id descending as a
        deterministic tie-break for runs saved within the same
        microsecond). Metadata columns only -- never input_json/result_json."""
        query = (
            "SELECT run_id, created_at, commodity, run_status FROM procurement_runs "
            "ORDER BY created_at DESC, run_id DESC"
        )
        params: tuple = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()

        return [
            RunSummary(run_id=r["run_id"], created_at=r["created_at"], commodity=r["commodity"], run_status=r["run_status"])
            for r in rows
        ]
