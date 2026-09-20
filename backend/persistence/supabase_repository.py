"""
Phase 8B -- PostgreSQL/Supabase-backed implementation of the
ProcurementRunRepository interface (backend/persistence/repository.py).

CONNECTION APPROACH (Phase 8A ADR-5, authoritative -- see
reports/phase8a_architecture_decision_record.md): this connects DIRECTLY
to the Supabase-hosted Postgres database via a standard PostgreSQL driver
(psycopg) using a connection string, not via Supabase's REST/PostgREST
client library and not by forwarding each caller's own JWT. FastAPI
remains the sole, consistent data-access point -- exactly the role it
already has today with SQLite -- using its own privileged server-side
connection with explicit `user_id` filtering as the PRIMARY ownership
enforcement layer once authentication exists, with Postgres Row Level
Security enabled as a second, independent layer (defense-in-depth).

PHASE 8F UPDATE: this class now reads, writes, and filters by `user_id` on
every method, using the exact `user_id` column Phase 8B's migration
already added (supabase/migrations/20260914120000_create_procurement_runs.sql
-- unmodified by this phase). `save_run` writes the caller-supplied
`user_id`; `get_run`/`list_runs` both include `user_id = %s` directly in
their SQL WHERE clause -- ownership is enforced by the query itself, never
by fetching a row first and checking its owner in Python afterward. This
is the PRIMARY ownership-enforcement layer (Phase 8A ADR-5): this class
connects with FastAPI's own privileged, RLS-bypassing connection (a plain
`DATABASE_URL` connection string, not a per-user forwarded JWT -- see
Section 15 of reports/phase8f_user_owned_persistence.md for the observed
connection architecture), so the Postgres RLS policies already defined on
`procurement_runs` are a second, independent defense-in-depth layer, not
the mechanism this class relies on for correctness.

Mirrors sqlite_repository.py's design exactly, on a different backend:
one short-lived connection per call (no persistent pool held across
requests, matching the same "no shared mutable connection state" reasoning
database.py already documents for SQLite), parameterized queries only, no
business logic of any kind -- this file only reads and writes rows. Unlike
sqlite_repository.py, this class does NOT create its table implicitly --
the `procurement_runs` schema is managed exclusively via the
version-controlled migration in supabase/migrations/, applied deliberately
by a human (Step 5/14 of this phase's own instructions: no auto-DDL against
a real cloud database).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from backend.api.serialization import to_json_safe
from backend.models.run_contracts import ProcurementRunInput, ProcurementRunResult
from backend.persistence.repository import RunSummary, StoredRun


class SupabaseProcurementRunRepository:
    """PostgreSQL-backed implementation, conforming to the
    ProcurementRunRepository interface (repository.py). `database_url` is
    a standard `postgresql://` connection string -- read from the
    environment by the caller (backend/api/dependencies.py), never
    hardcoded or logged by this class."""

    def __init__(self, database_url: str):
        self._database_url = database_url

    def save_run(self, user_id: str, run_input: ProcurementRunInput, run_result: ProcurementRunResult) -> str:
        """Persist one already-computed run, owned by `user_id`. Never
        recomputes, never mutates run_input/run_result -- to_json_safe
        reads them, it does not modify them. Returns the new run's ID."""
        run_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        input_payload = to_json_safe(run_input)
        result_payload = to_json_safe(run_result)

        with psycopg.connect(self._database_url) as conn:
            conn.execute(
                """
                INSERT INTO procurement_runs (
                    run_id, user_id, created_at, commodity, run_status,
                    eligible_vendor_count, candidate_group_count, selected_group_count,
                    input_json, result_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id, user_id, created_at, run_result.commodity_id, run_result.run_status,
                    run_result.eligible_vendor_count, run_result.candidate_group_count,
                    run_result.selected_group_count, Jsonb(input_payload), Jsonb(result_payload),
                ),
            )
            conn.commit()
        return run_id

    def get_run(self, user_id: str, run_id: str) -> Optional[StoredRun]:
        """Returns the stored run, but ONLY if it is owned by `user_id` --
        None otherwise, identically to a genuinely nonexistent run_id (so
        a caller can never distinguish "no such run" from "that run
        belongs to someone else"). Ownership is enforced directly in the
        WHERE clause, never by fetching the row first and checking its
        owner afterward. A genuine database/connection error (backend
        unreachable, malformed connection string, etc.) is NEVER converted
        into None here -- it propagates as a real psycopg.Error, so a
        connectivity failure is never misreported to a caller as "run not
        found" (which would silently turn a real service outage into an
        incorrect 404 at the API layer)."""
        with psycopg.connect(self._database_url, row_factory=dict_row) as conn:
            row = conn.execute(
                "SELECT run_id, created_at, commodity, run_status, input_json, result_json "
                "FROM procurement_runs WHERE run_id = %s AND user_id = %s",
                (run_id, user_id),
            ).fetchone()

        if row is None:
            return None

        return StoredRun(
            run_id=str(row["run_id"]),
            created_at=self._format_timestamp(row["created_at"]),
            commodity=row["commodity"],
            run_status=row["run_status"],
            input=row["input_json"],
            result=row["result_json"],
        )

    def list_runs(self, user_id: str, limit: Optional[int] = None) -> List[RunSummary]:
        """Newest first (created_at descending, run_id descending as a
        deterministic tie-break), filtered to runs owned by `user_id`
        only. Metadata columns only -- never input_json/result_json."""
        query = (
            "SELECT run_id, created_at, commodity, run_status FROM procurement_runs "
            "WHERE user_id = %s ORDER BY created_at DESC, run_id DESC"
        )
        params: tuple = (user_id,)
        if limit is not None:
            query += " LIMIT %s"
            params = (user_id, limit)

        with psycopg.connect(self._database_url, row_factory=dict_row) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            RunSummary(
                run_id=str(r["run_id"]),
                created_at=self._format_timestamp(r["created_at"]),
                commodity=r["commodity"],
                run_status=r["run_status"],
            )
            for r in rows
        ]

    @staticmethod
    def _format_timestamp(value) -> str:
        """Normalizes `created_at` to the same plain ISO-8601 string shape
        sqlite_repository.py already produces, regardless of whether the
        underlying driver returned a timezone-aware datetime.datetime
        (real psycopg, TIMESTAMPTZ column) or a plain string (a test
        double) -- so StoredRun/RunSummary's `created_at: str` contract
        (repository.py) holds identically for both implementations."""
        if isinstance(value, str):
            return value
        return value.isoformat()
