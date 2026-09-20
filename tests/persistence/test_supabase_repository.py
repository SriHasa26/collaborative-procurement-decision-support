"""
Phase 8B tests: the PostgreSQL/Supabase-backed repository implementation
(backend/persistence/supabase_repository.py).

CRITICAL ISOLATION RULE: none of these tests connect to a real Postgres
server or a real Supabase project. `psycopg.connect` is replaced with a
small in-memory fake (`FakeConnection`/`FakeCursor` below) that records
exactly what SQL/parameters were passed and returns pre-arranged results
-- this lets the repository's own SQL-building and row-mapping logic be
verified precisely, without any network access, real credentials, or a
real database. `DATABASE_URL` is never read or required by these tests.

Covers Phase 8B's required test areas:
  - Repository interface behavior (both implementations satisfy the same
    Protocol) -- test_both_implementations_satisfy_the_interface
  - Save operation constructs the correct persistence data
  - List operation
  - Single-run retrieval
  - Unknown run behavior
  - JSON serialization safety (real to_json_safe output, not fabricated)
  - Required database fields are correctly mapped
  - Errors are handled predictably (never masquerade as "not found")

Phase 8F adds (T14-T16 per the phase8f task spec): the save query writes
the given `user_id`, the list query filters by `user_id` in its WHERE
clause, and the single-run query filters by BOTH `run_id` AND `user_id`
in the same WHERE clause -- all verified against the exact SQL text and
parameters recorded by the FakeConnection below, never against a real
database.
"""

import psycopg
import pytest

from backend.models.run_contracts import ProcurementRunInput
from backend.persistence.repository import ProcurementRunRepository, RunSummary, StoredRun
from backend.persistence.sqlite_repository import SQLiteProcurementRunRepository
from backend.persistence.supabase_repository import SupabaseProcurementRunRepository
from backend.services.procurement_run import ProcurementRunService
from tests.fixtures.orchestration_fixtures import COMMODITY, CONFIG, CONTEXT, ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3

FAKE_DATABASE_URL = "postgresql://fake-user:fake-password@fake-host:5432/fake-db"
USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self._fetchone_result = fetchone_result
        self._fetchall_result = fetchall_result if fetchall_result is not None else []

    def fetchone(self):
        return self._fetchone_result

    def fetchall(self):
        return self._fetchall_result


class FakeConnection:
    """Records every (query, params) pair passed to execute(), and
    returns pre-arranged fetchone/fetchall results -- a test double for
    psycopg.Connection, never a real network connection."""

    def __init__(self, fetchone_result=None, fetchall_result=None, raise_on_execute=None):
        self.executed = []
        self.committed = False
        self._fetchone_result = fetchone_result
        self._fetchall_result = fetchall_result
        self._raise_on_execute = raise_on_execute

    def execute(self, query, params=None):
        if self._raise_on_execute is not None:
            raise self._raise_on_execute
        self.executed.append((query, params))
        return FakeCursor(self._fetchone_result, self._fetchall_result)

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def _run_input(submissions):
    return ProcurementRunInput(commodity=COMMODITY, context=CONTEXT, vendor_submissions=tuple(submissions), config=CONFIG)


def _real_run_result():
    """A real, fully-computed ProcurementRunResult -- reused from the
    orchestration fixtures already used by the SQLite persistence tests,
    so serialization safety (below) is checked against genuine decision-
    engine output, not a hand-built stand-in."""
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    return run_input, ProcurementRunService().run(run_input)


# --- Repository interface behavior ---
def test_both_implementations_satisfy_the_interface(tmp_path):
    sqlite_repo = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    supabase_repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)

    assert isinstance(sqlite_repo, ProcurementRunRepository)
    assert isinstance(supabase_repo, ProcurementRunRepository)


def test_supabase_repository_construction_does_not_connect():
    # Constructing the repository must not attempt any real connection --
    # it only stores the connection string, exactly like SQLite's
    # repository only stores a path (no query runs until a method is
    # called). No psycopg.connect patch is active here; if construction
    # tried to connect, this test would fail with a real network error.
    SupabaseProcurementRunRepository(FAKE_DATABASE_URL)


# --- Save operation: constructs the correct persistence data ---
def test_save_run_constructs_correct_insert(monkeypatch):
    fake_conn = FakeConnection()
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: fake_conn,
    )

    run_input, run_result = _real_run_result()
    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    run_id = repo.save_run(USER_A, run_input, run_result)

    assert run_id  # non-empty
    assert len(run_id) == 36  # standard UUID4 string length
    assert fake_conn.committed is True
    assert len(fake_conn.executed) == 1

    query, params = fake_conn.executed[0]
    assert "INSERT INTO procurement_runs" in query
    assert params[0] == run_id
    # Phase 8F (T14): the verified user_id is written as the row's owner.
    assert params[1] == USER_A
    assert params[3] == run_result.commodity_id
    assert params[4] == run_result.run_status
    assert params[5] == run_result.eligible_vendor_count
    assert params[6] == run_result.candidate_group_count
    assert params[7] == run_result.selected_group_count

    # JSON serialization safety: the wrapped payloads are the REAL,
    # already-verified to_json_safe() output -- plain JSON-safe dicts,
    # never a raw dataclass/Enum object reaching the driver.
    input_payload = params[8].obj  # psycopg.types.json.Jsonb wraps the dict as .obj
    result_payload = params[9].obj
    assert isinstance(input_payload, dict)
    assert isinstance(result_payload, dict)
    assert result_payload["run_status"] == run_result.run_status
    assert result_payload["final_selection"]["total_savings_rs"] == run_result.final_selection.total_savings_rs
    # No Enum/dataclass repr leaked anywhere in the serialized payload.
    import json
    dumped = json.dumps(result_payload)
    assert "DecisionState." not in dumped
    assert " object at 0x" not in dumped


# --- Single-run retrieval ---
def test_get_run_maps_row_to_stored_run(monkeypatch):
    fake_row = {
        "run_id": "11111111-1111-1111-1111-111111111111",
        "created_at": "2026-09-14T12:00:00+00:00",
        "commodity": "potato",
        "run_status": "COMPLETED",
        "input_json": {"commodity": {"commodity_id": "potato"}},
        "result_json": {"run_status": "COMPLETED", "commodity_id": "potato"},
    }
    fake_conn = FakeConnection(fetchone_result=fake_row)
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: fake_conn,
    )

    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    stored = repo.get_run(USER_A, "11111111-1111-1111-1111-111111111111")

    assert isinstance(stored, StoredRun)
    assert stored.run_id == fake_row["run_id"]
    assert stored.created_at == fake_row["created_at"]
    assert stored.commodity == "potato"
    assert stored.run_status == "COMPLETED"
    assert stored.input == fake_row["input_json"]
    assert stored.result == fake_row["result_json"]

    query, params = fake_conn.executed[0]
    # Phase 8F (T16): filters by BOTH run_id AND user_id in the same
    # WHERE clause -- never fetch-by-run_id-then-check-owner-in-Python.
    assert "WHERE run_id = %s AND user_id = %s" in query
    assert params == ("11111111-1111-1111-1111-111111111111", USER_A)


# --- Unknown run behavior ---
def test_get_run_returns_none_for_unknown_run(monkeypatch):
    fake_conn = FakeConnection(fetchone_result=None)
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: fake_conn,
    )

    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    assert repo.get_run(USER_A, "00000000-0000-0000-0000-000000000000") is None


def test_get_run_returns_none_for_a_run_owned_by_a_different_user(monkeypatch):
    """Phase 8F: the fake connection has no row matching (run_id, user_id)
    together -- exactly what the real WHERE clause would produce for a
    run that exists but is owned by someone else. Confirms the repository
    never distinguishes this from a genuinely unknown run_id."""
    fake_conn = FakeConnection(fetchone_result=None)
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: fake_conn,
    )

    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    assert repo.get_run(USER_B, "11111111-1111-1111-1111-111111111111") is None
    query, params = fake_conn.executed[0]
    assert params == ("11111111-1111-1111-1111-111111111111", USER_B)


# --- List operation ---
def test_list_runs_maps_rows_and_orders_newest_first(monkeypatch):
    fake_rows = [
        {"run_id": "b", "created_at": "2026-09-14T12:01:00+00:00", "commodity": "onion", "run_status": "COMPLETED"},
        {"run_id": "a", "created_at": "2026-09-14T12:00:00+00:00", "commodity": "potato", "run_status": "COMPLETED_NO_SELECTION"},
    ]
    fake_conn = FakeConnection(fetchall_result=fake_rows)
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: fake_conn,
    )

    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    summaries = repo.list_runs(USER_A)

    assert len(summaries) == 2
    assert all(isinstance(s, RunSummary) for s in summaries)
    assert summaries[0].run_id == "b"
    assert summaries[0].commodity == "onion"
    assert summaries[1].run_status == "COMPLETED_NO_SELECTION"

    query, params = fake_conn.executed[0]
    # Phase 8F (T15): filters by user_id in the WHERE clause.
    assert "WHERE user_id = %s" in query
    assert "ORDER BY created_at DESC, run_id DESC" in query
    assert "LIMIT" not in query
    assert params == (USER_A,)


def test_list_runs_applies_limit_clause(monkeypatch):
    fake_conn = FakeConnection(fetchall_result=[])
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: fake_conn,
    )

    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    repo.list_runs(USER_A, limit=5)

    query, params = fake_conn.executed[0]
    assert "LIMIT %s" in query
    assert params == (USER_A, 5)


# --- Errors are handled predictably ---
def test_get_run_propagates_real_database_errors_not_none(monkeypatch):
    connection_error = psycopg.OperationalError("simulated connection failure -- not a real network error")
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: (_ for _ in ()).throw(connection_error),
    )

    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    # A genuine connection failure must NEVER be silently reported as
    # "run not found" (None) -- that would misrepresent a service outage
    # as a 404 at the API layer. It must propagate as a real error.
    with pytest.raises(psycopg.OperationalError):
        repo.get_run(USER_A, "11111111-1111-1111-1111-111111111111")


def test_save_run_propagates_real_database_errors(monkeypatch):
    fake_conn = FakeConnection(raise_on_execute=psycopg.errors.UniqueViolation("simulated duplicate key"))
    monkeypatch.setattr(
        "backend.persistence.supabase_repository.psycopg.connect",
        lambda *args, **kwargs: fake_conn,
    )

    run_input, run_result = _real_run_result()
    repo = SupabaseProcurementRunRepository(FAKE_DATABASE_URL)
    with pytest.raises(psycopg.errors.UniqueViolation):
        repo.save_run(USER_A, run_input, run_result)
