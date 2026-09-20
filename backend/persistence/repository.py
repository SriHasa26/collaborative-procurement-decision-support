"""
Phase 6G -- persistence repository shapes.
Phase 8B -- formalized into an explicit interface (`ProcurementRunRepository`,
a `typing.Protocol`) plus the shared value types both implementations
produce, so the application/API layer can depend on the abstraction alone
and never needs to know whether persistence is backed by SQLite
(`sqlite_repository.SQLiteProcurementRunRepository`) or Supabase
PostgreSQL (`supabase_repository.SupabaseProcurementRunRepository`).
Phase 8F -- every method now takes an explicit `user_id` (the verified
identity from `backend.security.auth.AuthenticatedUser.user_id`, never
from request JSON -- see backend/api/routes/procurement.py) as its
ownership context. This is the minimal signature change needed to make
ownership enforcement possible at the persistence layer itself, per
reports/phase8a_architecture_decision_record.md ADR-5: application-level
`WHERE user_id = ...` filtering is the PRIMARY enforcement layer, Postgres
RLS a second, independent one -- not the reverse. `user_id` is threaded
through explicitly as a plain parameter on every call; no global or
thread-local "current user" state exists anywhere in this project.

This module intentionally contains NO database-specific code (no
`sqlite3`, no `psycopg`) -- it is the shared contract only. Neither
implementation is imported here, to avoid this module (and anything that
imports it, including `backend/api/routes/procurement.py`) accidentally
depending on a specific database driver.

Uses `typing.Protocol` (PEP 544, standard library, no new dependency)
rather than `abc.ABC`: structural typing means both implementations
satisfy this interface without needing to explicitly subclass it (they do
anyway, for documentation clarity), keeping the abstraction as low-ceremony
as the project's own "avoid premature abstraction" principle asks for --
justified now specifically because a second real implementation
(Supabase) exists starting this phase, not before.

Responsible ONLY for reading and writing procurement_runs rows -- no
validation, eligibility, geographic, group-formation, or decision logic
belongs anywhere near either implementation. No query in either
implementation ever branches on decision content.
"""

from dataclasses import dataclass
from typing import List, Optional, Protocol, runtime_checkable

from backend.models.run_contracts import ProcurementRunInput, ProcurementRunResult


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


@runtime_checkable
class ProcurementRunRepository(Protocol):
    """The persistence contract every implementation must satisfy. All
    queries in every implementation are parameterized -- no SQL is ever
    built via string interpolation of a caller-supplied value.

    Deliberately minimal: exactly the three operations the application
    actually uses today (save/get/list). No `update_run`, `delete_run`,
    `search_runs`, or pagination exists here -- none is needed by any
    current code path, and inventing speculative CRUD would contradict
    this phase's own "keep the interface minimal" instruction.

    Phase 8F: every method takes `user_id` as its first parameter -- the
    verified identity a caller (backend/api/routes/procurement.py) must
    obtain from `get_current_user()` and pass through explicitly. Ownership
    filtering happens INSIDE each implementation's own query (`WHERE
    user_id = ...`), not by fetching first and checking after -- see
    sqlite_repository.py/supabase_repository.py. `save_run` writes
    `user_id` as the row's owner; `get_run`/`list_runs` never return a row
    that does not belong to the given `user_id` (a legacy row with a NULL
    `user_id` -- see Phase 8B -- matches no real `user_id` filter and is
    therefore never returned to any authenticated caller)."""

    def save_run(self, user_id: str, run_input: ProcurementRunInput, run_result: ProcurementRunResult) -> str:
        """Persist one already-computed run, owned by `user_id`. Never
        recomputes, never mutates run_input/run_result. Returns the new
        run's ID."""
        ...

    def get_run(self, user_id: str, run_id: str) -> Optional[StoredRun]:
        """Returns the stored run, but ONLY if it is owned by `user_id` --
        otherwise None, identically to a genuinely nonexistent run_id (a
        clear, typed, repository-level "not found" signal that
        deliberately does not distinguish "does not exist" from "exists
        but belongs to someone else", per this phase's own IDOR-avoidance
        requirement). Must never let a raw database driver error
        masquerade as "not found"; only a genuinely absent/not-owned row
        returns None."""
        ...

    def list_runs(self, user_id: str, limit: Optional[int] = None) -> List[RunSummary]:
        """Newest first (created_at descending, run_id descending as a
        deterministic tie-break), filtered to runs owned by `user_id`
        only. Metadata columns only -- never input_json/result_json."""
        ...
