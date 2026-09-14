# Phase 6G — Database & Persistence Layer

**Date:** 2026-09-14
**Scope:** Add SQLite persistence for procurement analysis runs — save, list, and retrieve — layered around the existing, unmodified Phase 6E `ProcurementRunService`. Infrastructure only: no business logic, no ORM, no cloud database, no authentication, no frontend.

---

## 1. Purpose

Every `POST /procurement/analyze` call (Phase 6F) previously computed a result and immediately discarded it. Phase 6G adds durable storage so a run's original input and complete result can be listed and retrieved later — for traceability and for a future caller (a future dashboard, audit tool, or script) to inspect past analyses without re-running them.

## 2. Scope

In scope: a `procurement_runs` SQLite table, a `ProcurementRunRepository` with `save_run`/`get_run`/`list_runs`, and two new HTTP endpoints (`GET /procurement/runs`, `GET /procurement/runs/{run_id}`) plus a persistence side-effect added to the existing `POST /procurement/analyze`. Out of scope (confirmed absent — Section 16): any database beyond SQLite, an ORM, run history normalization into multiple relational tables, authentication, a frontend, and any change to Phase 6A–6D's mathematics or Phase 6E's orchestration logic.

## 3. Database Technology Choice

**SQLite, via Python's built-in `sqlite3` module — no ORM.** Reasoning: (1) this phase's own spec explicitly requires SQLite and asks that SQLAlchemy be introduced only if inspection proves it necessary; (2) the persistence model is deliberately one table with two JSON columns (Section 4) — an ORM's relational-mapping machinery has nothing to map here, since the payload is stored as an opaque JSON snapshot, not as ORM-managed relational rows; (3) `sqlite3` is part of the Python standard library, so no new dependency was added for it (`requirements.txt` unchanged for this reason — see Section 12 note). A file-based SQLite database also matches the single-process, stateless API from Phase 6F with no additional infrastructure to run or configure.

## 4. Database Schema

One table, `procurement_runs`:

```sql
CREATE TABLE IF NOT EXISTS procurement_runs (
    run_id                  TEXT PRIMARY KEY,
    created_at              TEXT NOT NULL,
    commodity               TEXT NOT NULL,
    run_status               TEXT NOT NULL,
    eligible_vendor_count    INTEGER NOT NULL,
    candidate_group_count    INTEGER NOT NULL,
    selected_group_count     INTEGER NOT NULL,
    input_json               TEXT NOT NULL,
    result_json              TEXT NOT NULL
)
```

`eligible_vendor_count`, `candidate_group_count`, and `selected_group_count` are copied verbatim from `ProcurementRunResult`'s own existing fields (Phase 6E) — no new business concept, just three already-computed integers exposed as queryable columns for lightweight filtering without parsing `result_json`. No other metadata field was added.

## 5. Persistence Architecture

```
backend/persistence/
    __init__.py
    database.py     -- sqlite3 connection + schema management (initialize_database, get_connection)
    repository.py   -- ProcurementRunRepository (save_run / get_run / list_runs), RunSummary, StoredRun
```

`database.py` knows only how to open a connection and ensure the table exists — it contains no query that inspects run content. `repository.py` is the only component permitted to run SQL against this table; every query is parameterized (`?` placeholders — Section 10). Neither file imports anything from `backend/core/`, `backend/services/decision_engine.py`, `group_formation.py`, `decision_evaluation.py`, or `selection.py`.

## 6. Serialization Strategy

`repository.save_run` reuses Phase 6F's existing `backend.api.serialization.to_json_safe` to convert `ProcurementRunInput`/`ProcurementRunResult` into JSON-safe structures before `json.dumps`, rather than writing a second converter. This is a deliberate reuse decision, not an oversight: `to_json_safe` is a generic, pure-Python dataclass/Enum/tuple/set walker with no FastAPI- or HTTP-specific code, already tested against exactly these contracts in Phase 6F (`tests/api/test_procurement_api.py::test_t8_json_serialization_...`). Importing it from `backend/persistence/` does mean persistence depends on a module physically located under `backend/api/` — a reversal of the usual web-layering direction — but it introduces no cycle (`backend/api/serialization.py` imports nothing from `backend/persistence/` or `backend/services/`) and avoids a second, drifting copy of the same conversion logic. This is noted explicitly here rather than silently accepted; a future phase could relocate `to_json_safe` to a neutral shared module if stricter layering is later required, but doing so was not necessary for Phase 6G and was not done, per the "do not modify unless required" default.

## 7. Repository Responsibilities

`ProcurementRunRepository` (constructed with a database path; calls `initialize_database` on construction, so it is always safe to instantiate):

- `save_run(run_input, run_result) -> str` — generates a `uuid.uuid4()` run ID, a UTC ISO-8601 `created_at` timestamp, serializes both objects (Section 6) without mutating them, and inserts one row. Returns the new run's ID.
- `get_run(run_id) -> Optional[StoredRun]` — returns `None` (a clear, typed, repository-level "not found" signal) rather than raising or letting a raw `sqlite3.Error` escape for the ordinary missing-row case.
- `list_runs(limit=None) -> List[RunSummary]` — metadata columns only (`run_id`, `created_at`, `commodity`, `run_status`), ordered `created_at DESC, run_id DESC` (the second key is a deterministic tie-break for two runs saved within the same timestamp resolution, not a business rule).

No repository method contains a conditional that depends on `decision_state`, `run_status`, or any other business value — every row is written and read as an opaque snapshot.

## 8. API Integration

`backend/api/dependencies.py` adds one function, `get_repository()`, used via FastAPI's `Depends()` in `backend/api/routes/procurement.py` — the standard, no-extra-framework way to make the database path swappable per-request. Tests override it via `app.dependency_overrides[get_repository] = lambda: <tmp_path repository>` (Section 11); nothing hard-codes the production path into a route handler. `POST /procurement/analyze` now calls `repository.save_run(run_input, result)` **after** `ProcurementRunService.run()` has already produced `result` — `ProcurementRunService.run()` itself was not modified (confirmed by inspection: `backend/services/procurement_run.py` has zero changes this phase).

## 9. Endpoint Behavior

| Endpoint | Behavior |
|---|---|
| `POST /procurement/analyze` | Unchanged response shape from Phase 6F (the same `ProcurementRunResult` JSON); persists as a side effect; still 200 for every structurally valid request regardless of analytical outcome |
| `GET /procurement/runs` | Returns a list of `{run_id, created_at, commodity, run_status}`, newest first — never `input`/`result` JSON |
| `GET /procurement/runs/{run_id}` | Returns `{run_id, created_at, commodity, run_status, input, result}` for a known run; `404` with a plain `{"detail": "procurement run not found: <id>"}` for an unknown one |

Verified directly (automated tests, Section 12, and a manual end-to-end check against an isolated temporary database): `run_id` does **not** appear in the `POST /procurement/analyze` response body — that endpoint's contract is unchanged from Phase 6F; a run's ID is only discoverable via `GET /procurement/runs`, matching this phase's own endpoint design.

## 10. Database Safety

Every SQL statement uses `?` parameter placeholders — no string interpolation of a caller-supplied value into a query anywhere in `repository.py`. No endpoint accepts or executes arbitrary SQL. No response includes the database file path. `test_no_sql_injection_via_run_id` sends a `run_id` containing a `DROP TABLE` fragment and confirms it is treated as an inert lookup value (returns "not found"; the table still exists afterward).

## 11. Test Isolation

`tests/persistence/test_repository.py` uses pytest's `tmp_path` fixture directly, constructing every `ProcurementRunRepository` against `tmp_path / "procurement.db"`. `tests/api/conftest.py` adds an **autouse** fixture, `isolated_repository`, that overrides `get_repository` via `app.dependency_overrides` for every test under `tests/api/` — including the pre-existing Phase 6F test file, `tests/api/test_procurement_api.py`, which now triggers a persistence side effect on every `POST /procurement/analyze` call and would otherwise have silently written to the real database. Confirmed directly: `data/app/` does not exist on disk before, during, or after the full test run (`ls data/app/` → "No such file or directory" both before and after `pytest -q`).

## 12. Test Results

```
16 new tests passed, 0 failed, 0 skipped
122 total: passed, 0 failed, 0 skipped
```

| Suite | Tests | Result |
|---|---|---|
| Phase 6A–6F (unchanged) | 106 | ✅ all pass |
| Phase 6G — `tests/persistence/test_repository.py` | 9 | ✅ all pass |
| Phase 6G — `tests/api/test_procurement_runs_api.py` | 7 | ✅ all pass |
| **Total** | **122** | **122 passed, 0 failed, 0 skipped** |

No existing test was modified. `data/raw/` and `data/processed/` were not read or written by any new file (confirmed by inspection — the only mention of either path in any new file is an explanatory code comment in `database.py` stating they are deliberately avoided).

## 13. Files Created

- `backend/persistence/__init__.py`, `backend/persistence/database.py`, `backend/persistence/repository.py`
- `backend/api/dependencies.py`
- `tests/persistence/__init__.py`, `tests/persistence/test_repository.py`
- `tests/api/conftest.py`, `tests/api/test_procurement_runs_api.py`
- This report

## 14. Files Modified

- `backend/api/routes/procurement.py` — added the persistence call to the existing `analyze_procurement` handler, plus two new route handlers (`list_runs`, `get_run`). The pre-existing `/analyze` logic (build input → call `ProcurementRunService.run()` → serialize) is unchanged; only the persistence call and its `Depends(get_repository)` parameter were added.

No file under `backend/core/`, `backend/models/`, `backend/services/` (including `procurement_run.py`), `backend/api/main.py`, `backend/api/schemas.py`, `backend/api/serialization.py`, or any prior test/report file was changed. `requirements.txt` was **not** modified — `sqlite3` is part of the Python standard library and no other new package was needed.

## 15. Important Findings

No blocking interface problem was encountered. `ProcurementRunResult` already exposed exactly the three derived counts (`eligible_vendor_count`, `candidate_group_count`, `selected_group_count`) this phase's optional-metadata-column guidance allowed, so no new derivation logic was needed. Reusing `to_json_safe` (Section 6) was the one deliberate architectural trade-off worth flagging honestly — it is a safe, non-cyclical reuse, but it does mean `backend/persistence/` has a dependency on a module physically located under `backend/api/`.

## 16. Scope Verification

Confirmed by inspection: no file under `backend/persistence/` or the modified `backend/api/routes/procurement.py` contains a Haversine calculation, a cost/savings formula, MOQ or freshness logic, WAIT/EXPAND resolution, overlap resolution, demand estimation, or an eligibility check — every one of those still runs exactly once, inside `ProcurementRunService.run()`, unmodified. No SQL query branches on `decision_state`, `run_status`, or any other business value. `ProcurementRunService.run()` (`backend/services/procurement_run.py`) has zero changes this phase. Phase 6A–6D's mathematics and Phase 6E's orchestration logic are untouched. No authentication, user account, Firebase/Supabase, cloud infrastructure, frontend, React, or dashboard code exists anywhere in this phase's new or modified files. The closed Potato ML experiment and `data/raw/`/`data/processed/` were not read or touched.

---

**Files read for this phase:** `reports/phase5f_system_architecture.md`, `reports/phase5f_module_interfaces.md`, `reports/phase5f_traceability_and_implementation_plan.md`, `reports/phase6a_core_foundation_report.md`, `reports/phase6b_validation_and_eligibility_report.md`, `reports/phase6c_group_formation_report.md`, `reports/phase6d_procurement_decision_and_selection.md`, `reports/phase6e_end_to_end_orchestration.md`, `reports/phase6f_fastapi_api.md`, `backend/models/run_contracts.py`, `backend/services/procurement_run.py`, `backend/api/routes/procurement.py`, `backend/api/serialization.py`, `backend/api/schemas.py`, `requirements.txt`.
**Files modified:** `backend/api/routes/procurement.py` only, plus the new `backend/persistence/`, `backend/api/dependencies.py`, `tests/persistence/`, `tests/api/conftest.py`, `tests/api/test_procurement_runs_api.py` additions and this report.
