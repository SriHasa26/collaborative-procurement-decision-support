"""
Phase 6G tests: SQLite persistence layer
(backend/persistence/database.py, backend/persistence/sqlite_repository.py).

Covers required test cases T1-T6 (numbering per the Phase 6G task spec).
Every test uses a pytest `tmp_path`-based database file -- NEVER the
production `data/app/procurement.db` -- so these tests are isolated,
repeatable, and leave no trace on the real database.

T2-T4 run the REAL Phase 6E orchestration (ProcurementRunService.run) on
real fixture data -- persistence is tested against an actual computed
result, not a hand-built stand-in, so these tests also prove the
repository can round-trip everything Phase 6A-6E actually produce.

Phase 8B: `ProcurementRunRepository` (backend/persistence/repository.py)
is now the shared interface; this file was updated to import and
instantiate the concrete `SQLiteProcurementRunRepository`
(backend/persistence/sqlite_repository.py) instead -- a mechanical
rename only, no test behavior or assertion changed.

Phase 8F: every `save_run`/`get_run`/`list_runs` call below now passes an
explicit `user_id` (USER_A), mechanically -- these T1-T6 tests are about
persistence/orchestration round-tripping, not ownership, so USER_A is used
throughout and no existing assertion changed. Dedicated cross-user
ownership tests (T17-style, per the Phase 8F task spec) are appended at
the bottom of this file.
"""

import sqlite3

from backend.models.run_contracts import ProcurementRunInput
from backend.persistence.database import get_connection, initialize_database
from backend.persistence.sqlite_repository import SQLiteProcurementRunRepository
from backend.services.procurement_run import ProcurementRunService
from tests.fixtures.orchestration_fixtures import (
    ABSTAIN_NO_EVIDENCE,
    COMMODITY,
    CONFIG,
    CONTEXT,
    ELIGIBLE_1,
    ELIGIBLE_2,
    ELIGIBLE_3,
    VALIDATION_ERROR_NEGATIVE_QTY,
)

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def _run_input(submissions):
    return ProcurementRunInput(
        commodity=COMMODITY, context=CONTEXT, vendor_submissions=tuple(submissions), config=CONFIG,
    )


# --- T1: database initialization ---
def test_t1_initialization_creates_directory_and_table(tmp_path):
    db_path = tmp_path / "nested" / "does" / "not" / "exist" / "procurement.db"
    assert not db_path.parent.exists()

    initialize_database(db_path)

    assert db_path.parent.exists()
    assert db_path.exists()

    conn = get_connection(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    finally:
        conn.close()
    assert "procurement_runs" in tables


def test_t1_initialization_is_safe_to_call_repeatedly(tmp_path):
    db_path = tmp_path / "procurement.db"
    initialize_database(db_path)

    repository = SQLiteProcurementRunRepository(db_path)
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    run_id = repository.save_run(USER_A, run_input, ProcurementRunService().run(run_input))

    # Re-initializing must not drop the table or the row just inserted.
    initialize_database(db_path)
    initialize_database(db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT run_id FROM procurement_runs WHERE run_id = ?", (run_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None


def test_t1_initialization_adds_user_id_column_to_pre_phase8f_database(tmp_path):
    """Non-destructive schema evolution (backend/persistence/database.py's
    _ensure_user_id_column): a database file created before Phase 8F --
    simulated here by creating the table with the exact pre-8F schema
    directly, bypassing initialize_database -- must gain a usable
    `user_id` column, with any pre-existing row left otherwise intact,
    the next time initialize_database runs."""
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE procurement_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                commodity TEXT NOT NULL,
                run_status TEXT NOT NULL,
                eligible_vendor_count INTEGER NOT NULL,
                candidate_group_count INTEGER NOT NULL,
                selected_group_count INTEGER NOT NULL,
                input_json TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO procurement_runs VALUES ('legacy-run', '2026-01-01T00:00:00+00:00', 'potato', 'COMPLETED', 2, 1, 1, '{}', '{}')"
        )
        conn.commit()
    finally:
        conn.close()

    initialize_database(db_path)

    conn = get_connection(db_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(procurement_runs)").fetchall()}
        row = conn.execute("SELECT run_id, user_id, commodity FROM procurement_runs WHERE run_id = 'legacy-run'").fetchone()
    finally:
        conn.close()

    assert "user_id" in columns
    assert row["run_id"] == "legacy-run"  # pre-existing row untouched
    assert row["commodity"] == "potato"
    assert row["user_id"] is None  # no owner fabricated for a pre-existing row


# --- T2: save run ---
def test_t2_save_run_via_real_orchestration(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    run_result = ProcurementRunService().run(run_input)

    run_id = repository.save_run(USER_A, run_input, run_result)

    assert run_id  # non-empty
    assert len(run_id) == 36  # standard UUID4 string length ("xxxxxxxx-xxxx-...")

    conn = get_connection(tmp_path / "procurement.db")
    try:
        row = conn.execute("SELECT * FROM procurement_runs WHERE run_id = ?", (run_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["user_id"] == USER_A
    assert row["commodity"] == run_result.commodity_id
    assert row["run_status"] == run_result.run_status
    assert row["eligible_vendor_count"] == run_result.eligible_vendor_count
    assert row["candidate_group_count"] == run_result.candidate_group_count
    assert row["selected_group_count"] == run_result.selected_group_count


def test_save_run_does_not_mutate_input_or_result(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    run_result = ProcurementRunService().run(run_input)

    original_status = run_result.run_status
    original_selected = run_result.final_selection.selected_group_ids

    repository.save_run(USER_A, run_input, run_result)

    assert run_result.run_status == original_status
    assert run_result.final_selection.selected_group_ids == original_selected


# --- T3: input traceability ---
def test_t3_input_traceability(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3, ABSTAIN_NO_EVIDENCE])
    run_result = ProcurementRunService().run(run_input)

    run_id = repository.save_run(USER_A, run_input, run_result)
    stored = repository.get_run(USER_A, run_id)

    stored_vendor_ids = {v["vendor_id"] for v in stored.input["vendor_submissions"]}
    original_vendor_ids = {v.vendor_id for v in run_input.vendor_submissions}
    assert stored_vendor_ids == original_vendor_ids

    assert stored.input["commodity"]["commodity_id"] == run_input.commodity.commodity_id
    assert stored.input["context"]["date"] == run_input.context.date
    assert stored.input["config"]["d_max_km"] == run_input.config.d_max_km


# --- T4: result traceability ---
def test_t4_result_traceability(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3, ABSTAIN_NO_EVIDENCE, VALIDATION_ERROR_NEGATIVE_QTY])
    run_result = ProcurementRunService().run(run_input)

    run_id = repository.save_run(USER_A, run_input, run_result)
    stored = repository.get_run(USER_A, run_id)

    assert stored.result["run_status"] == run_result.run_status

    stored_abstained = {v["vendor_id"] for v in stored.result["batch_eligibility"]["abstained_vendors"]}
    assert stored_abstained == {v.vendor_id for v in run_result.batch_eligibility.abstained_vendors}

    stored_candidate_groups = stored.result["group_formation"]["candidate_groups"]
    assert len(stored_candidate_groups) == len(run_result.group_formation.candidate_groups)

    stored_selected = stored.result["final_selection"]["selected_group_ids"]
    assert tuple(stored_selected) == run_result.final_selection.selected_group_ids
    assert stored.result["final_selection"]["total_savings_rs"] == run_result.final_selection.total_savings_rs

    # Base + final decision state both preserved (no reasoning flattened away).
    first_evaluated = stored.result["final_selection"]["all_evaluated_results"][0]
    assert "decision_state" in first_evaluated["decision"]
    assert "final_decision_state" in first_evaluated


# --- T5: list runs ---
def test_t5_list_runs_newest_first_lightweight(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")

    ids = []
    for submissions in ([ELIGIBLE_1, ELIGIBLE_2], [ELIGIBLE_1, ELIGIBLE_3], [ELIGIBLE_2, ELIGIBLE_3]):
        run_input = _run_input(submissions)
        ids.append(repository.save_run(USER_A, run_input, ProcurementRunService().run(run_input)))

    summaries = repository.list_runs(USER_A)

    assert {s.run_id for s in summaries} == set(ids)
    for s in summaries:
        assert s.commodity == "tomato"
        assert s.run_status  # non-empty

    # Verify the SQL ordering matches (created_at DESC, run_id DESC)
    # computed independently in Python from the actual stored rows -- this
    # stays correct even if the host clock's resolution makes two saves
    # land on the identical timestamp (a legitimate possibility this
    # phase's own tie-break, run_id DESC, exists to handle).
    expected_order = sorted(summaries, key=lambda s: (s.created_at, s.run_id), reverse=True)
    assert [s.run_id for s in summaries] == [s.run_id for s in expected_order]

    # Lightweight only -- RunSummary carries no input/result JSON at all.
    assert not hasattr(summaries[0], "input")
    assert not hasattr(summaries[0], "result")


# --- T6: unknown run ---
def test_t6_unknown_run_returns_none(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    result = repository.get_run(USER_A, "00000000-0000-0000-0000-000000000000")
    assert result is None


def test_no_sql_injection_via_run_id(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    # A malicious-looking run_id must be treated as an opaque string, never
    # interpreted as SQL -- the table must still exist and be queryable.
    malicious = "x'; DROP TABLE procurement_runs; --"
    assert repository.get_run(USER_A, malicious) is None

    conn = get_connection(tmp_path / "procurement.db")
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    finally:
        conn.close()
    assert "procurement_runs" in tables


def test_no_sql_injection_via_user_id(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    malicious_user_id = "x'; DROP TABLE procurement_runs; --"
    assert repository.list_runs(malicious_user_id) == []

    conn = get_connection(tmp_path / "procurement.db")
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    finally:
        conn.close()
    assert "procurement_runs" in tables


# --- Phase 8F: cross-user ownership (T17-style, per phase8f task spec) ---


def test_save_run_records_the_given_owner(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])

    run_id_a = repository.save_run(USER_A, run_input, ProcurementRunService().run(run_input))
    run_id_b = repository.save_run(USER_B, run_input, ProcurementRunService().run(run_input))

    conn = get_connection(tmp_path / "procurement.db")
    try:
        row_a = conn.execute("SELECT user_id FROM procurement_runs WHERE run_id = ?", (run_id_a,)).fetchone()
        row_b = conn.execute("SELECT user_id FROM procurement_runs WHERE run_id = ?", (run_id_b,)).fetchone()
    finally:
        conn.close()
    assert row_a["user_id"] == USER_A
    assert row_b["user_id"] == USER_B


def test_list_runs_is_scoped_to_the_given_user(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])

    run_id_a = repository.save_run(USER_A, run_input, ProcurementRunService().run(run_input))
    run_id_b = repository.save_run(USER_B, run_input, ProcurementRunService().run(run_input))

    assert {s.run_id for s in repository.list_runs(USER_A)} == {run_id_a}
    assert {s.run_id for s in repository.list_runs(USER_B)} == {run_id_b}


def test_get_run_denies_cross_user_access_as_not_found(tmp_path):
    repository = SQLiteProcurementRunRepository(tmp_path / "procurement.db")
    run_input = _run_input([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    run_id_a = repository.save_run(USER_A, run_input, ProcurementRunService().run(run_input))

    # The owner can retrieve it.
    assert repository.get_run(USER_A, run_id_a) is not None
    # A different user gets the identical "not found" signal as a
    # genuinely nonexistent run_id -- not an error, not partial data.
    assert repository.get_run(USER_B, run_id_a) is None


def test_legacy_null_owner_row_is_not_visible_to_any_authenticated_user(tmp_path):
    """A row saved before ownership existed (Phase 8B) has user_id = NULL.
    SQL's `NULL = ?` is never true, so such a row must not appear in any
    authenticated user's list_runs or be retrievable via get_run -- no
    owner is fabricated or guessed for it."""
    db_path = tmp_path / "procurement.db"
    repository = SQLiteProcurementRunRepository(db_path)

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO procurement_runs "
            "(run_id, user_id, created_at, commodity, run_status, eligible_vendor_count, "
            "candidate_group_count, selected_group_count, input_json, result_json) "
            "VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("legacy-null-owner", "2026-01-01T00:00:00+00:00", "potato", "COMPLETED", 2, 1, 1, "{}", "{}"),
        )
        conn.commit()
    finally:
        conn.close()

    assert repository.get_run(USER_A, "legacy-null-owner") is None
    assert repository.get_run(USER_B, "legacy-null-owner") is None
    assert "legacy-null-owner" not in {s.run_id for s in repository.list_runs(USER_A)}
    assert "legacy-null-owner" not in {s.run_id for s in repository.list_runs(USER_B)}
