# Phase 8F — Verified User-Owned Procurement Run Persistence

**Date:** 2026-09-14
**Scope:** Thread the verified identity Phase 8D already produces through to persistence, so every procurement run is owned by exactly one user and cross-user access is denied at the application layer. Frontend authentication, real multi-user browser testing, and any database migration/RLS change are explicitly out of scope and not implemented here.

---

## 1. Purpose

Phase 8D proved *who* is making a request. It never used that fact for anything — every authenticated user could list and retrieve every run. Phase 8F closes that gap: `current_user.user_id` (from `get_current_user()`, backend/security/auth.py) now flows into every persistence operation, and both repository implementations enforce ownership directly in their queries.

## 2. Scope

Implemented: verified-identity propagation into `save_run`/`get_run`/`list_runs`; a minimal, necessary change to `ProcurementRunRepository`'s signatures; ownership filtering in both `SQLiteProcurementRunRepository` and `SupabaseProcurementRunRepository`; non-destructive SQLite schema evolution (`user_id` column); route integration; 18 new offline tests covering cross-user isolation, legacy-row handling, and request-JSON-spoofing resistance.

Not implemented (see Section 24): frontend login/signup/logout, a React auth context, the Supabase JS client, protected frontend routes, a user profile UI, deployment, any new business logic, any database migration/RLS change, and any ORM.

## 3. Previous Security Limitation Closed

Documented explicitly in `reports/phase8d_fastapi_jwt_authentication.md` Section 23: "Any authenticated user (any real Supabase user with a valid token) can currently list and retrieve any run." This is now false — `get_run`/`list_runs` filter by the caller's own verified `user_id` inside their SQL, and `save_run` always writes the caller's own verified `user_id` as the owner.

## 4. Ownership Architecture

Four layers, as specified:

1. **JWT verification** (`backend/security/jwt_verifier.py`, Phase 8D, unchanged) — proves the token is genuine.
2. **Verified user identity** (`backend/security/auth.py`'s `get_current_user()`, Phase 8D, unchanged) — extracts `user_id` from the token's `sub` claim only.
3. **Application-level repository filtering** (new in this phase) — `SQLiteProcurementRunRepository`/`SupabaseProcurementRunRepository` include `user_id` directly in every query's `WHERE` clause. **This is the primary, load-bearing enforcement layer** — the application never relies on RLS alone (Section 15/16).
4. **Supabase RLS** (Phase 8B, unmodified) — a second, independent layer for the Supabase backend specifically; still not exercised by any real authenticated Supabase Auth session end-to-end (Section 16).

## 5. Verified User Identity Flow

```
Authorization: Bearer <token>
        |
get_current_user()  (backend/security/auth.py, Phase 8D -- unmodified)
        |
current_user.user_id   (a plain string, function-local)
        |
repository.save_run(current_user.user_id, run_input, result)
repository.list_runs(current_user.user_id)
repository.get_run(current_user.user_id, run_id)
        |
WHERE user_id = ...   (inside the repository implementation's own SQL)
```

`current_user.user_id` is passed as an ordinary explicit function argument at every step (`backend/api/routes/procurement.py`). No global variable, module-level cache, `contextvars`, or thread-local is used anywhere to carry identity — confirmed by inspection: `grep -rn "contextvar\|threading.local\|global " backend/` finds nothing identity-related. JWT verification is called exactly once per request, by the existing `get_current_user` dependency; this phase does not call `verify_access_token` or decode a token anywhere else.

## 6. Repository Interface Changes

`backend/persistence/repository.py`'s `ProcurementRunRepository` Protocol changed from:

```python
def save_run(self, run_input, run_result) -> str: ...
def get_run(self, run_id: str) -> Optional[StoredRun]: ...
def list_runs(self, limit: Optional[int] = None) -> List[RunSummary]: ...
```

to:

```python
def save_run(self, user_id: str, run_input, run_result) -> str: ...
def get_run(self, user_id: str, run_id: str) -> Optional[StoredRun]: ...
def list_runs(self, user_id: str, limit: Optional[int] = None) -> List[RunSummary]: ...
```

`user_id` is the first parameter, matching the task's own suggested convention. This is the minimal change that makes ownership possible: no new method was added, `RunSummary`/`StoredRun` (the response value types) are **unchanged** — they still carry no `user_id` field, so nothing new leaks into an API response (Section 17 of the original 8D-carried-forward instructions, restated here for 8F).

## 7. Save-Run Ownership Behavior

`POST /procurement/analyze`: after `ProcurementRunService().run()` produces a result (decision-engine logic, completely unaware of identity), the handler calls `repository.save_run(current_user.user_id, run_input, result)`. Both repository implementations write `user_id` as part of the same `INSERT` that writes every other column — there is no separate "assign owner" step that could be skipped or raced.

## 8. List-Runs Ownership Behavior

`GET /procurement/runs`: `repository.list_runs(current_user.user_id)`. Both implementations add `WHERE user_id = ?`/`WHERE user_id = %s` to the existing `ORDER BY created_at DESC, run_id DESC` query — the ordering semantics from Phase 6G/8B are otherwise unchanged. Filtering happens in the query itself, never by fetching every row and filtering in Python.

## 9. Single-Run Ownership Behavior

`GET /procurement/runs/{run_id}`: `repository.get_run(current_user.user_id, run_id)`. Both implementations' `SELECT` includes `WHERE run_id = ? AND user_id = ?` (SQLite) / `WHERE run_id = %s AND user_id = %s` (Supabase) — a single query checks both conditions together, never "fetch by run_id, then check the owner field in Python."

## 10. Cross-User Access Behavior

Verified directly with two distinct, independently-signed JWTs in `tests/security/test_ownership.py`: User A's runs never appear in User B's list (and vice versa); User A cannot retrieve User B's run by ID (and vice versa). Each repository's own query makes this structurally impossible to get wrong at the call site — there is no "oops, forgot to check ownership" path, because the query itself never returns a non-owned row in the first place.

## 11. Safe 404 Behavior

`get_run` returns `None` for **both** "run does not exist" and "run exists but belongs to someone else" — these two cases are indistinguishable to any caller, by construction (Section 9's combined `WHERE` clause never lets the repository know which case occurred). `backend/api/routes/procurement.py`'s `get_run` handler raises the same `HTTPException(404, ...)` for both, exactly as it already did pre-8F for a genuinely unknown `run_id`. No `403` is ever returned for cross-user access — this avoids confirming to a caller that a given `run_id` even exists, closing the IDOR/information-leakage path ADR-3 (`reports/phase8a_architecture_decision_record.md`) was written to prevent.

## 12. Supabase Repository Implementation

`backend/persistence/supabase_repository.py` — all three methods updated:
- `save_run(user_id, run_input, run_result)`: `INSERT INTO procurement_runs (run_id, user_id, created_at, ...)`.
- `get_run(user_id, run_id)`: `SELECT ... WHERE run_id = %s AND user_id = %s`.
- `list_runs(user_id, limit=None)`: `SELECT ... WHERE user_id = %s ORDER BY created_at DESC, run_id DESC [LIMIT %s]`.

All parameterized via psycopg's own placeholder substitution (`%s` + a params tuple) — no query is ever built by string interpolation of `user_id` or `run_id`. Verified against the exact SQL text and parameter tuples recorded by `tests/persistence/test_supabase_repository.py`'s `FakeConnection` test double (no real Postgres connection).

## 13. SQLite Compatibility

The pre-8F SQLite schema (`backend/persistence/database.py`) had **no `user_id` column at all** (confirmed by reading `_SCHEMA` directly before making any change). Two things were needed:

1. **New databases**: `_SCHEMA`'s `CREATE TABLE` now includes `user_id TEXT` (nullable — SQLite has no native UUID type; `run_id` is already stored the same way).
2. **Existing databases** (a real, already-created `data/app/procurement.db`, or any other pre-8F file): `initialize_database()` now also calls `_ensure_user_id_column()`, which checks `PRAGMA table_info(procurement_runs)` and runs `ALTER TABLE procurement_runs ADD COLUMN user_id TEXT` only if the column is missing. `ADD COLUMN` in SQLite never drops or rewrites existing rows — every pre-existing row simply gets `user_id = NULL`. This was tested directly: `test_t1_initialization_adds_user_id_column_to_pre_phase8f_database` creates a table with the exact pre-8F schema, inserts a row, runs the new `initialize_database()`, and confirms the row survives untouched with `user_id` now present and NULL.

No file was deleted, no data was dropped, and `data/app/procurement.db` (the real local database, if it exists) is not touched by anything in this phase beyond this same non-destructive column addition the next time the application starts.

## 14. Legacy NULL-Owner Rows

Any row with `user_id = NULL` (every row saved before Phase 8F, and any row Phase 8B's own Supabase migration left nullable) is **never returned** by any authenticated query: `WHERE user_id = ?` never matches SQL `NULL` in either SQLite or Postgres (`NULL = 'some-uuid'` evaluates to `NULL`/not-true, never `TRUE`). This was verified directly, not just asserted: `test_legacy_null_owner_row_is_not_visible_to_any_authenticated_user` (SQLite, direct repository) and `test_t10_legacy_null_owner_row_is_not_exposed` (full HTTP layer) both insert a real NULL-owner row and confirm it is invisible to both of two distinct authenticated users, via both `get_run` (404) and `list_runs` (absent from the list). No code anywhere guesses, fabricates, or assigns an owner to such a row.

## 15. RLS vs. Application-Level Filtering

Application-level filtering (Section 4, Layer 3) is the primary enforcement mechanism for both repositories — it is what actually determines the result of every query this backend runs, and it was independently tested (Sections 10–11) without any dependency on RLS behavior. Postgres RLS (Phase 8B, unmodified) is a second, independent layer that would still apply if some *other* client connected to the same database using a normal (non-privileged) authenticated Postgres role — but this backend's own queries do not depend on it, per ADR-5.

## 16. Database Connection / RLS Observations

Inspected `backend/api/dependencies.py` and `backend/persistence/supabase_repository.py` directly, per this phase's own explicit instruction not to guess: `get_repository()` reads a single `DATABASE_URL` environment variable and passes it, unmodified, to `SupabaseProcurementRunRepository(database_url)`, which in turn calls `psycopg.connect(self._database_url)` with no additional role-switching, no `SET ROLE`, and no per-request JWT forwarding anywhere in the code. **The code itself makes no assumption about which Postgres role that connection string authenticates as** — that is determined entirely by which connection string value the operator puts in `DATABASE_URL`.

This phase did not independently verify which role the user's real `DATABASE_URL` actually uses, and could not do so without connecting to the real project with real credentials, which is outside this phase's offline-testing constraints. Consistent with Phase 8A ADR-5's own stated assumption (carried forward, not re-derived here): Supabase's standard "connection string" (Database Settings → Connection string) authenticates as the `postgres` role, which owns every table it creates and therefore bypasses RLS entirely regardless of policy content, unless a table has `FORCE ROW LEVEL SECURITY` set (the Phase 8B migration does not set this). If that assumption holds, RLS currently provides no protection for *this backend's own* queries at all — which is exactly why Section 15's application-level filtering, not RLS, is treated as the primary layer, and why this phase does not claim RLS was meaningfully exercised. No credential, password, or `DATABASE_URL` value was printed, logged, or read by any test in this phase.

## 17. Request JSON Spoofing Protection

`ProcurementAnalysisRequest` (`backend/api/schemas.py`) still has no `user_id` field (unchanged by this phase) and Pydantic's default `extra="ignore"` behavior means a client-supplied `"user_id"` field is silently dropped before the handler ever runs. More fundamentally: the handler never reads `payload.user_id` under any circumstance — only `current_user.user_id` (from the verified JWT) is ever passed to `save_run`. Verified directly by `test_t11_spoofed_user_id_in_request_body_does_not_change_ownership`: User A sends a request body claiming `"user_id": "<User B's UUID>"`; the run is saved under User A's real, verified identity, is invisible to User B's list, and is visible in User A's own list.

## 18. Offline Testing Strategy

All new tests reuse Phase 8D's existing offline JWT/JWKS infrastructure (`tests/security/conftest.py`'s `fake_jwks` fixture: a locally-generated RSA keypair, a fake in-memory JWKS server, and a monkeypatched `urllib.request.urlopen` — no real network, no real Supabase project) — no second, parallel authentication test system was built. Two distinct real UUIDs are generated per test (`uuid.uuid4()`) and signed as two independent tokens against the same fake JWKS, giving genuine, independently-verified two-user scenarios. Persistence-layer tests (`tests/persistence/`) use pytest's `tmp_path` for SQLite and the existing `FakeConnection` double for Supabase (Phase 8B's own pattern) — no real database connection anywhere.

## 19. Test Cases

| # | Case | Location |
|---|------|----------|
| T1 | User A's saved run is stored under User A | `tests/security/test_ownership.py` |
| T2 | User B's saved run is stored under User B | `tests/security/test_ownership.py` |
| T3 | User A's list shows only User A's runs | `tests/security/test_ownership.py` |
| T4 | User B's list shows only User B's runs | `tests/security/test_ownership.py` |
| T5 | User A retrieves own run — success | `tests/security/test_ownership.py` |
| T6 | User B retrieves own run — success | `tests/security/test_ownership.py` |
| T7 | User A retrieves User B's run — 404 | `tests/security/test_ownership.py` |
| T8 | User B retrieves User A's run — 404 | `tests/security/test_ownership.py` |
| T9 | Unknown run ID — 404 | `tests/security/test_ownership.py` |
| T10 | Legacy NULL-owner row invisible to any user | `tests/security/test_ownership.py`, `tests/persistence/test_repository.py` |
| T11 | Spoofed `user_id` in request JSON has no effect | `tests/security/test_ownership.py` |
| T12 | Missing authentication — 401 | Already covered, `tests/security/test_auth.py` (not duplicated) |
| T13 | `GET /health` public — 200 | Already covered, `tests/security/test_auth.py` (not duplicated) |
| T14 | Supabase save query receives verified user_id | `tests/persistence/test_supabase_repository.py::test_save_run_constructs_correct_insert` |
| T15 | Supabase list query filters by user_id | `tests/persistence/test_supabase_repository.py::test_list_runs_maps_rows_and_orders_newest_first` |
| T16 | Supabase get query filters by run_id AND user_id | `tests/persistence/test_supabase_repository.py::test_get_run_maps_row_to_stored_run`, `::test_get_run_returns_none_for_a_run_owned_by_a_different_user` |
| T17 | SQLite ownership filtering behaves identically | `tests/persistence/test_repository.py` (`test_save_run_records_the_given_owner`, `test_list_runs_is_scoped_to_the_given_user`, `test_get_run_denies_cross_user_access_as_not_found`) |
| T18 | Decision engine behavior unaffected | Full suite passes unchanged; `backend/core/`/`backend/services/` untouched (confirmed via `git status`) |

Additional edge tests added: SQL-injection resistance via a malicious `user_id` value (`test_no_sql_injection_via_user_id`); non-destructive schema evolution of a pre-8F SQLite file (`test_t1_initialization_adds_user_id_column_to_pre_phase8f_database`).

## 20. Test Results

- **Previous (pre-Phase-8F) baseline:** 157 passed.
- **New tests added:** 18.
- **Final:** `python -m pytest -q` → **175 passed, 0 failed, 0 skipped.**

## 21. Dependencies Added

**NONE.** `requirements.txt` was not modified in this phase. No ORM, ORM-adjacent library, Supabase Python client, Firebase SDK, Redis, or Celery was added or considered necessary.

## 22. Security Audit (20 checks)

1. **`user_id` comes only from verified identity** — confirmed (Section 5); no code path reads `payload.user_id` anywhere.
2. **Request JSON cannot assign ownership** — confirmed (Section 17); `test_t11_...` proves it directly.
3. **New authenticated runs always receive verified `user_id`** — confirmed (Section 7); the `INSERT` writes it unconditionally as part of the single insert statement.
4. **User A cannot list User B's runs** — confirmed (T3/T4).
5. **User B cannot list User A's runs** — confirmed (T3/T4).
6. **User A cannot retrieve User B's run** — confirmed (T7).
7. **User B cannot retrieve User A's run** — confirmed (T8).
8. **Cross-user access returns safe 404** — confirmed (Section 11); never 403.
9. **Unknown runs return 404** — confirmed (T9).
10. **Legacy NULL-owner rows are not exposed** — confirmed (T10, Section 14).
11. **Supabase queries filter by `user_id`** — confirmed (T15).
12. **Single-run query filters by BOTH `run_id` and `user_id`** — confirmed (T16).
13. **SQLite behavior matches ownership semantics** — confirmed (T17).
14. **RLS is not relied upon as the only security layer** — confirmed (Section 15/16); application-level filtering is primary and independently tested without any live RLS behavior involved.
15. **JWT verification is reused, not duplicated** — confirmed; `backend/security/jwt_verifier.py`/`auth.py` were not modified, and no second decode/verify call was added anywhere in this phase.
16. **Decision engine has no user/auth logic** — confirmed; `backend/core/` and `backend/services/` show zero changes (`git status --short backend/core/ backend/services/` — empty).
17. **Frontend remains unchanged** — confirmed (Section 25 below); `git status --short frontend/` shows only pre-existing changes from earlier phases, none from this session.
18. **No database migration/schema/RLS modification occurred** — confirmed; `supabase/migrations/` untouched (Section 26). The SQLite schema *was* evolved, non-destructively, as explicitly anticipated and permitted by this phase's own Section 12/13 instructions — this is not a database migration in the Supabase/version-controlled-SQL sense.
19. **No real credentials appear in source/tests/reports** — confirmed; every test uses locally-generated UUIDs, a fake JWKS, and either `tmp_path` SQLite or a mocked Postgres connection.
20. **All tests pass offline** — confirmed; zero network calls, zero real Supabase access, `python -m pytest -q` run with no internet dependency.

## 23. Problems or Ambiguities Found

The SQLite schema had no `user_id` column at all before this phase (unlike Postgres, where Phase 8B already added it). This was anticipated by the task's own Section 12 ("inspect the existing SQLite schema carefully... if SQLite schema must evolve..."), and resolved with the same non-destructive, nullable-column pattern Phase 8B already established for Postgres — not treated as a blocking ambiguity, since the safe approach (check-then-`ALTER TABLE ADD COLUMN`) is a standard, well-defined SQLite idiom with no destructive interpretation possible. This reasoning is recorded here rather than silently applied.

The Postgres connection's actual RLS-bypass status (Section 16) remains an assumption carried forward from Phase 8A/8B/8D, not independently re-verified in this phase — flagged explicitly rather than silently treated as settled fact.

## 24. Known Limitations

- **No frontend authentication exists.** A browser cannot yet obtain a token, so no real user has ever exercised any of this through the actual UI.
- **RLS has not been tested against a real authenticated Supabase session.** All ownership guarantees demonstrated here are for this backend's own application-level filtering; Phase 8G (per the existing roadmap) is where RLS itself would be exercised end-to-end.
- **The Postgres connection's RLS-bypass status is an assumption, not a freshly-verified fact** (Section 16, Section 23).
- **Real multi-user behavior against the live Supabase project is untested** — every cross-user test here uses locally-generated identities and either SQLite or a mocked Postgres connection.

## 25. What Phase 8F Intentionally Does NOT Implement

Frontend login, signup, logout, a React auth context, the Supabase JS client, protected frontend routes, a user profile page, password reset, email verification UI, OAuth/Google login, Firebase, deployment, any new decision-engine/business logic, any database redesign, and any ORM. `git status --short frontend/` was run and confirms zero files under `frontend/` were created or modified during this phase (all listed changes there predate this session, carried over from earlier phases).

## 26. Recommended Next Phase

Per the existing roadmap, Phase 8G (RLS and security testing against real authenticated Supabase sessions) is the natural next step — it is the phase that would resolve Section 16/23's open RLS-bypass assumption with real evidence rather than a carried-forward assumption. Phase 8C (frontend authentication UI) remains an independent, unstarted prerequisite for any real end-to-end (browser-driven) multi-user testing.

**Multi-user security is NOT fully complete** as of this phase: frontend authentication does not exist, real RLS behavior has not been tested with multiple real Supabase users, and true end-to-end multi-user testing (a real browser, a real login, a real second account) belongs to a later phase.

---

## Phase 8F Summary

### 1. Status
Complete. Verified-identity propagation, user-owned persistence, cross-user isolation, and repository-level ownership filtering are implemented for both SQLite and Supabase repositories; all 18 required test areas are covered.

### 2. Previous security limitation closed
Phase 8D's own documented limitation — "any authenticated user can list/retrieve any run" — no longer holds; ownership is now enforced at the persistence-query level for every route.

### 3. Ownership architecture implemented
Four layers: JWT verification → verified identity → application-level repository filtering (primary) → Supabase RLS (defense-in-depth, unmodified). See Section 4.

### 4. Verified user identity flow
`Authorization` header → `get_current_user()` (unmodified from Phase 8D) → `current_user.user_id` → passed explicitly as a plain argument into `save_run`/`get_run`/`list_runs`. No global or thread-local identity state anywhere.

### 5. Repository interface changes
`ProcurementRunRepository.save_run/get_run/list_runs` all now take `user_id: str` as their first parameter. `RunSummary`/`StoredRun` are unchanged (no `user_id` field added to API responses).

### 6. Save-run ownership behavior
`POST /procurement/analyze` writes `current_user.user_id` as the row's owner in the same `INSERT` as every other field — never a separate, skippable step.

### 7. List-runs ownership behavior
`GET /procurement/runs` filters by `WHERE user_id = ...` inside the repository's own query; ordering (`created_at DESC, run_id DESC`) is unchanged.

### 8. Single-run ownership behavior
`GET /procurement/runs/{run_id}` filters by `WHERE run_id = ... AND user_id = ...` in one query — never fetch-then-check.

### 9. Cross-user access behavior
Verified directly with two distinct, independently-signed JWTs: neither user can list or retrieve the other's runs (T1–T8).

### 10. Legacy NULL-owner behavior
A NULL `user_id` never matches any real `user_id` filter in SQL; such rows are invisible to every authenticated user via both `get_run` and `list_runs`, verified directly by inserting a real legacy row and querying it as two different users (T10). No owner is fabricated or guessed.

### 11. Supabase repository changes
`save_run` writes `user_id`; `list_runs` filters by `user_id`; `get_run` filters by `run_id` AND `user_id` together — all via parameterized `%s` placeholders, verified against a mocked `psycopg` connection (T14–T16).

### 12. SQLite compatibility
`user_id TEXT` (nullable) added to the `CREATE TABLE` for new databases; `_ensure_user_id_column()` non-destructively `ALTER TABLE ADD COLUMN`s it into any pre-existing database file, verified to preserve existing rows exactly. `data/app/procurement.db` is never deleted or recreated.

### 13. Request JSON spoofing protection
A request body's `user_id` field (which `ProcurementAnalysisRequest` does not even define) has zero effect on ownership; only `current_user.user_id` (from the verified JWT) is ever used, proven with a real spoofing attempt across two real users (T11).

### 14. Dependencies added
NONE.

### 15. Tests added
18 (`tests/security/test_ownership.py`: 11; `tests/persistence/test_repository.py`: +6; `tests/persistence/test_supabase_repository.py`: +1).

### 16. Test results
Previous test count: 157
New tests: 18
Final: 175

passed: 175
failed: 0
skipped: 0

### 17. Files created
`tests/security/test_ownership.py`, `reports/phase8f_user_owned_persistence.md`.

### 18. Files modified
`backend/persistence/repository.py`, `backend/persistence/sqlite_repository.py`, `backend/persistence/supabase_repository.py`, `backend/persistence/database.py`, `backend/api/routes/procurement.py`, `tests/api/conftest.py` (exported `FAKE_TEST_USER`, no assertion changed), `tests/api/test_procurement_runs_api.py` (2 call sites updated to pass `user_id`), `tests/persistence/test_repository.py`, `tests/persistence/test_supabase_repository.py`.

### 19. Frontend modifications
NONE. `git status --short frontend/` shows only pre-existing changes from earlier phases; nothing under `frontend/` was read for editing, written, or edited in this phase.

### 20. Database modifications
No Supabase migration, schema change, or RLS change occurred; `supabase/migrations/` is untouched. The **SQLite** schema was evolved non-destructively (a nullable `user_id` column added, via `ALTER TABLE ADD COLUMN` guarded by a `PRAGMA table_info` check) — explicitly anticipated and permitted by this phase's own instructions, and verified to preserve all existing rows.

### 21. Security audit
All 20 checks pass — see Section 22 above for the itemized list.

### 22. Problems or ambiguities found
The SQLite schema had no `user_id` column pre-8F (unlike Postgres); resolved with the same non-destructive pattern Phase 8B already used for Postgres, not treated as a blocking ambiguity. The Postgres connection's RLS-bypass status remains a carried-forward assumption from Phase 8A/8B/8D, not independently re-verified here (Section 16).

### 23. Known limitations
No frontend authentication exists; RLS has not been tested against a real authenticated Supabase session; the RLS-bypass assumption for the backend's own connection is unconfirmed; real multi-user behavior against the live Supabase project is untested.

### 24. Recommended next phase
Phase 8G (RLS and security testing against real authenticated Supabase sessions) — it is the natural next step to resolve the open RLS-bypass assumption with real evidence. Phase 8C (frontend authentication UI) remains an independent, unstarted prerequisite for real end-to-end multi-user testing.
