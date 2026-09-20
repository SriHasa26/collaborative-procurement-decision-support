# Phase 8B — Supabase Database Foundation & Persistence Migration

**Date:** 2026-09-14
**Scope:** Formalize the persistence repository interface, add a PostgreSQL/Supabase-backed implementation alongside the existing SQLite one, and create the version-controlled schema migration. Authentication, frontend changes, and full multi-user security are explicitly out of scope and not implemented.

---

## 1. Phase Objective

Phase 8A designed the target architecture; Phase 8B builds its database foundation. Concretely: make the persistence layer's implicit contract explicit, add a real Postgres implementation conforming to that contract, and produce the schema as reviewable, version-controlled SQL — all without touching the decision engine, the API contract, the frontend, or introducing any authentication.

## 2. Existing Architecture Inspected

Read completely before writing any code, per this phase's own instruction: `reports/phase8a_supabase_multiuser_architecture.md`, `reports/phase8a_architecture_decision_record.md`, `reports/phase8a_migration_roadmap.md` (all authoritative for this phase — no decision already made there was reopened). Also inspected directly: `backend/persistence/{database,repository}.py`, `backend/api/{dependencies,main}.py`, `backend/api/routes/procurement.py`, `backend/api/schemas.py`, `tests/persistence/test_repository.py`, `tests/api/conftest.py`, `requirements.txt`, `.gitignore`, and the repository root for any pre-existing `supabase/`/`migrations/`/`database/`/`sql/` directory (none existed).

## 3. Files Inspected

`backend/persistence/database.py`, `backend/persistence/repository.py` (pre-Phase-8B version), `backend/api/dependencies.py`, `backend/api/routes/procurement.py`, `backend/api/main.py`, `backend/api/schemas.py`, `tests/persistence/test_repository.py`, `tests/api/conftest.py`, `requirements.txt`, `.gitignore`.

## 4. Repository Abstraction Design

`backend/persistence/repository.py` is now the shared interface module only: a `typing.Protocol` (`@runtime_checkable`, PEP 544, standard library — no new dependency) named `ProcurementRunRepository`, plus the two value types both implementations produce (`RunSummary`, `StoredRun`), which moved here unchanged. The interface is deliberately minimal — exactly the three operations the application already uses (`save_run`, `get_run`, `list_runs`); no `update_run`, `delete_run`, `search_runs`, or pagination was added, per this phase's explicit "do not create unnecessary CRUD" instruction. `@runtime_checkable` was added specifically so both implementations' conformance can be verified directly with `isinstance()` in tests (Section 16).

`backend/api/routes/procurement.py` needed **zero changes** — it already imports `ProcurementRunRepository` from `repository.py` purely as a type annotation for its `Depends()` parameters; that import path and usage remain valid whether the name refers to a concrete class or a Protocol.

## 5. SQLite Preservation Strategy

The existing SQLite implementation was **extracted, not deleted or rewritten**: its exact code moved from `repository.py` into a new file, `backend/persistence/sqlite_repository.py`, with the class renamed `ProcurementRunRepository` → `SQLiteProcurementRunRepository` (matching this phase's own suggested naming). Every method body, query, and semantic is byte-for-byte identical to Phase 6G's original — this is a pure extract-and-rename, confirmed by the fact that all pre-existing SQLite regression tests (T1–T6 plus the SQL-injection test) pass unchanged after only their import path/class name was updated (`tests/persistence/test_repository.py`, `tests/api/conftest.py` — a mechanical rename, not a behavior or assertion change). `backend/persistence/database.py` (schema init, connection handling) was **not modified at all**.

## 6. Supabase Repository Design

`backend/persistence/supabase_repository.py` implements `SupabaseProcurementRunRepository`, conforming to the same interface. **Connection approach (Phase 8A ADR-5, authoritative):** a direct PostgreSQL connection via `psycopg` (v3), using a `DATABASE_URL` connection string — not Supabase's REST/PostgREST client library, and not per-user JWT forwarding. This keeps FastAPI as the single, consistent data-access point, exactly matching its existing role with SQLite.

**Dependency chosen: `psycopg[binary]`, used synchronously — not the already-installed `asyncpg`.** This environment already had `asyncpg` present (apparently pre-installed in anticipation), but it was deliberately **not** used: `asyncpg` is async-only, and adopting it would force converting every route handler and repository method to `async def` — an unrelated, unrequested architectural change this phase's own "avoid unnecessary async conversion" instruction explicitly warns against. `psycopg` (the modern, actively-maintained successor to `psycopg2`) supports a fully synchronous API by default, matching the existing entirely-synchronous FastAPI/repository code with zero conversion needed. This is documented as a deliberate deviation from what a pre-installed package might suggest, not an oversight.

Design mirrors `sqlite_repository.py` closely: one short-lived connection per call (no persistent pool held across requests, matching `database.py`'s own existing "no shared mutable connection state" reasoning), parameterized queries only (`%s` placeholders, never string interpolation), no business logic of any kind. One deliberate difference: `SupabaseProcurementRunRepository.__init__` performs **no DDL** (unlike SQLite's auto-create-if-missing behavior) — the Postgres schema is managed exclusively by the version-controlled migration (Section 8), never created implicitly against a real cloud database.

**Serialization reuse:** `to_json_safe` (`backend/api/serialization.py`, Phase 6F) is reused exactly as `sqlite_repository.py` already does — no second serializer was written. The pre-existing persistence→api import direction (documented and accepted in the Phase 6G report) is unchanged; Phase 8A did not flag this as requiring correction, and refactoring it was correctly out of this phase's minimal-change scope.

**Error handling:** a genuine `psycopg` error (connection failure, constraint violation, etc.) is never caught and converted into `None`/an empty result — it propagates as a real exception. This is intentional and tested (Section 16): silently mapping a connectivity failure to "run not found" would misreport a real service outage as a 404 at the API layer.

## 7. PostgreSQL Schema Design

Per Phase 8A's authoritative decision (ADR-8): the existing single-table, JSON-column design is preserved, not normalized — `input_json`/`result_json` remain opaque, immutable snapshots, upgraded from SQLite's `TEXT` to Postgres-native `JSONB`. `user_id` is added in preparation for future ownership.

```sql
create table if not exists procurement_runs (
    run_id                 uuid primary key default gen_random_uuid(),
    user_id                uuid references auth.users(id) on delete cascade,
    created_at             timestamptz not null default now(),
    commodity              text not null,
    run_status             text not null,
    eligible_vendor_count  integer not null,
    candidate_group_count  integer not null,
    selected_group_count   integer not null,
    input_json             jsonb not null,
    result_json            jsonb not null
);

create index if not exists idx_procurement_runs_user_created
    on procurement_runs (user_id, created_at desc);
```

`run_id`/`created_at` are still generated in **Python** by the repository code (`uuid.uuid4()`, `datetime.now(timezone.utc).isoformat()`), matching `sqlite_repository.py` exactly for behavioral consistency between both implementations — the SQL `default` clauses exist only as a schema-level safety net, not the primary generation path.

## 8. SQL Migration Location

`supabase/migrations/20260914120000_create_procurement_runs.sql` — no `migrations/`, `supabase/`, `database/`, or `sql/` directory existed before this phase; `supabase/migrations/` was chosen as the new location because it matches the **official Supabase CLI's own migration folder convention** (timestamp-prefixed filename), so this file will slot in correctly if the project ever adopts the Supabase CLI, without renaming. **The migration was written only — it was not applied to any real database by this phase** (Section 21 gives exact manual instructions). It contains no destructive statement (no `DROP`, `DELETE`, `TRUNCATE`) and uses `IF NOT EXISTS` throughout, so it is safe to re-run.

## 9. Exact Table Structure

See Section 7's SQL verbatim — nine columns plus one composite index, exactly matching `RunSummary`/`StoredRun`'s existing fields plus `user_id`. No column beyond what Phase 8A's schema design and the existing `ProcurementRunResult`-derived counts already require.

## 10. JSONB / TIMESTAMPTZ / UUID Choices and Reasoning

- **`JSONB` for `input_json`/`result_json`:** Postgres-native, indexable if ever needed later (not committed to now), and `psycopg`'s default type adapters (confirmed directly by inspecting the installed `psycopg.types.json` module before writing any code) transparently convert Python `dict`↔JSONB in both directions — no manual `json.dumps`/`json.loads` needed in `supabase_repository.py`, unlike the SQLite version which stores plain `TEXT` and must serialize/parse explicitly.
- **`TIMESTAMPTZ` for `created_at`:** a proper temporal type, timezone-aware; the existing code already produces UTC ISO-8601 strings, so this is a compatible upgrade, not a behavior change. `SupabaseProcurementRunRepository._format_timestamp()` normalizes whatever the driver returns (a real `datetime.datetime` from a live connection, or a plain string from a test double) back to the same plain ISO-8601 string shape `StoredRun`/`RunSummary` already contractually promise, so the interface's `created_at: str` field means the same thing regardless of which implementation produced it.
- **`UUID` for `run_id`/`user_id`:** matches the existing `uuid.uuid4()`-generated string IDs exactly (Postgres's `uuid` type round-trips with Python's `str(uuid.uuid4())` values with no conversion surprises); `user_id references auth.users(id)` ties directly into Supabase Auth's own user table, per Phase 8A's design.

## 11. `user_id` Handling — Why Client-Provided `user_id` Is Prohibited, and a Documented Deviation From Phase 8A's Literal Wording

**`backend/api/schemas.py`'s `ProcurementAnalysisRequest` was not modified and has no `user_id` field** (confirmed: `grep -n "user_id" backend/api/schemas.py` finds nothing). Accepting a client-supplied `user_id` would let any caller read or write data as any other user by editing one JSON field — a textbook Insecure Direct Object Reference (IDOR) vulnerability (Phase 8A ADR-3, unchanged, not reopened). Neither `SupabaseProcurementRunRepository.save_run` nor any route handler accepts or references a `user_id` parameter anywhere in this phase's code — there is no verified identity to supply one with, since authentication does not exist yet.

**One deliberate, documented deviation from Phase 8A's literal schema wording:** the architecture report's example schema listed `user_id UUID NOT NULL`. The actual migration in this phase uses `user_id uuid` **without** `NOT NULL`. Reason: Phase 8B's own persistence code (by explicit, correct design — Section 6) never writes `user_id` at all, since no authenticated identity exists to write. A `NOT NULL` constraint would make every `INSERT` from `SupabaseProcurementRunRepository.save_run()` fail immediately, making the table unusable by this phase's own code. This is judged **not** to materially affect security: a nullable column the application never populates is not itself a vulnerability, and the RLS policies (Section 12) correctly deny access to any row regardless of whether `user_id` is `NULL` or a mismatched value (`auth.uid() = NULL` is never true in SQL). The migration's own comment block documents this explicitly and flags that a future migration, applied alongside the authentication phase, should add `NOT NULL` once every write path can supply a real, verified `user_id`.

## 12. RLS Status

**Row Level Security is enabled, with real (not fake) SELECT/INSERT policies — but this is schema preparation, not a claim that multi-user security is complete or has been end-to-end verified.** These are two different things, stated here explicitly:

| | Status |
|---|---|
| Database structure ready (table, columns, index, RLS enabled, correct policies defined) | **Yes** |
| Full multi-user security verified end-to-end (a real authenticated request, a real second user, a real cross-user-access-denied test) | **No — not possible yet, since no authentication exists anywhere in this project** |

The two policies created:
```sql
create policy "procurement_runs_select_own" on procurement_runs
    for select using (auth.uid() = user_id);

create policy "procurement_runs_insert_own" on procurement_runs
    for insert with check (auth.uid() = user_id);
```
These reference **only** `auth.uid()` — Supabase's own trusted, JWT-verified session function — never a client-supplied value, so they are not "fake" or insecure policies; they are the real, correct policies, simply **unexercised** by any live authenticated traffic so far (nothing in this project produces a real Supabase session yet). No `UPDATE`/`DELETE` policy was created (ADR-6 — no such operation exists in the current interface). End-to-end verification against real users is explicitly deferred to Phase 8G (`reports/phase8a_migration_roadmap.md`), not claimed complete here.

## 13. Dependency Injection Design

`backend/api/dependencies.py`'s `get_repository()` now selects explicitly based on one environment variable:
```python
def get_repository() -> ProcurementRunRepository:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return SupabaseProcurementRunRepository(database_url)
    return SQLiteProcurementRunRepository(DEFAULT_DB_PATH)
```
No factory class, no configuration framework — the simplest mechanism that satisfies the requirement, per this phase's own "do not invent an overly complex factory pattern" instruction. `DATABASE_URL` unset (its state in this project's test/CI environment, and an empty string, tested explicitly) → SQLite; set → Supabase. FastAPI's existing `Depends(get_repository)` wiring in the route handlers required no change.

## 14. Environment Variable Names Used

| File | Variable | Status |
|---|---|---|
| `backend/.env.example` (new) | `DATABASE_URL` | **Active** — read by `get_repository()` |
| `backend/.env.example` (new) | `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY` | Documented, commented out — reserved for the authentication phase; **no code reads these yet** |
| `frontend/.env.example` | `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` | Already present (added by the user before this phase, observed but not modified — see Section 20) |

## 15. Secret Handling

No secret value was hardcoded, printed, logged, or copied into any report or source file. The user's own `frontend/.env`/`.env.example` were **not read or inspected** by this phase's own actions beyond the IDE-provided change notices already visible in the conversation (per this phase's explicit "do not inspect or print the user's .env file contents" instruction — no `cat`/`Read` was performed on either file). A repository-wide search for fragments of the real Supabase project URL/key visible in those notices confirmed **zero matches** in any tracked file. `.gitignore`'s existing `.env` / `.env.*` / `!.env.example` pattern was verified (via `git check-ignore`) to correctly ignore both the new `backend/.env` (hypothetically) and correctly keep `backend/.env.example` trackable — no `.gitignore` change was needed.

## 16. Test Strategy

No automated test connects to a real Postgres server or a real Supabase project. `SupabaseProcurementRunRepository`'s tests patch `psycopg.connect` with a small in-memory `FakeConnection`/`FakeCursor` test double (`tests/persistence/test_supabase_repository.py`) that records exactly what SQL/parameters were passed and returns pre-arranged results — this verifies the repository's own SQL-building and row-mapping logic precisely, with zero network access and zero real credentials. `DATABASE_URL` is never read or required by any test.

## 17. New Tests (12)

| File | Tests | Covers |
|---|---|---|
| `tests/persistence/test_supabase_repository.py` | 9 | Interface conformance (`isinstance` against the `Protocol`); construction performs no connection; `save_run` builds the correct `INSERT` with correctly-typed/ordered parameters and a real, `to_json_safe`-serialized (leak-free) payload; `get_run` maps a row to `StoredRun` correctly and returns `None` only for a genuinely missing row; `list_runs` maps rows to `RunSummary` and applies the `LIMIT` clause only when requested; a real `psycopg.OperationalError`/`UniqueViolation` propagates from `get_run`/`save_run` rather than being swallowed into a misleading `None`/silent success |
| `tests/api/test_dependencies.py` | 3 | `get_repository()` resolves to SQLite when `DATABASE_URL` is unset or empty, and to Supabase when it is set — using a fake connection string that is never actually connected to |

## 18. Full Test Results

```
Previous test count:  122
New tests added:       12
Final test count:     134
Failures:               0
Skipped:                0
```
```
pytest -q -> 134 passed in 6.26s
```
All 122 pre-existing tests pass unchanged (including every original SQLite persistence test, now exercising `SQLiteProcurementRunRepository` via an updated import only — no assertion was altered). No existing test was modified to make it pass; the only changes to existing test files were the mechanical class-name/import-path updates required by the interface formalization (Section 5).

## 19. Files Created

- `backend/persistence/sqlite_repository.py`
- `backend/persistence/supabase_repository.py`
- `backend/.env.example`
- `supabase/migrations/20260914120000_create_procurement_runs.sql`
- `tests/persistence/test_supabase_repository.py`
- `tests/api/test_dependencies.py`
- `reports/phase8b_supabase_database_foundation.md` (this report)

## 20. Files Modified

- `backend/persistence/repository.py` — reduced to the shared interface (`Protocol`) + `RunSummary`/`StoredRun` value types; the SQLite implementation moved out (Section 5).
- `backend/api/dependencies.py` — `get_repository()` now selects an implementation based on `DATABASE_URL` (Section 13).
- `requirements.txt` — added `psycopg[binary]>=3.1`, with reasoning documented inline (Section 6).
- `tests/persistence/test_repository.py`, `tests/api/conftest.py` — mechanical rename to `SQLiteProcurementRunRepository` (Section 5); no assertion changed.

**Not modified:** `backend/persistence/database.py`, `backend/persistence/__init__.py`, `backend/api/main.py`, `backend/api/routes/procurement.py`, `backend/api/schemas.py`, anything under `backend/core/`, `backend/services/`, `backend/models/`, and everything under `frontend/` (observed only, per Section 15 — `frontend/.env`/`frontend/.env.example` already contained Supabase values added by the user before this phase began; nothing under `frontend/` was touched by this phase's own actions).

## 21. Dependencies Added

`psycopg[binary]>=3.1` — the only new dependency, added to `requirements.txt` (Section 6 explains why this driver, not `asyncpg` despite it already being present, and not the `supabase` Python client library, per Phase 8A ADR-5). No ORM, no SQLAlchemy, no async framework, no unrelated package was added.

## 22. Known Limitations

- RLS policies are defined but **not yet exercised by any real authenticated request** (Section 12) — this is expected at this stage, not a defect, and is called out explicitly rather than glossed over.
- `user_id` is nullable for now (Section 11) — a deliberate, documented, reasoned deviation from Phase 8A's literal example schema, to be tightened in the authentication phase.
- The migration has not been applied to any real database by this phase (manual application instructions: Section 24). Until applied, `SupabaseProcurementRunRepository` cannot actually be used against a real Supabase project (it will work correctly once the table exists — verified via the mocked test suite's precise SQL/parameter assertions, not via a live connection).
- No automated test exercises `SupabaseProcurementRunRepository` against a *real* Postgres instance (by design, per this phase's explicit "must not connect to the real Supabase project" instruction) — only a real, live Postgres run (manual, by the user, after applying the migration) would fully confirm end-to-end wire compatibility beyond what the mocked tests already verify structurally.

## 23. What Remains for Future Phases

Per `reports/phase8a_migration_roadmap.md`'s roadmap (unchanged, not redesigned here): Phase 8C (frontend Supabase Auth UI), Phase 8D (FastAPI JWT verification), Phase 8E (this phase largely completes 8E's persistence-migration portion; remaining: applying the migration to a real project and exercising it live), Phase 8F (wiring the verified `user_id` from 8D into this phase's repository calls — `save_run`'s signature will need to accept and write a real `user_id` at that point, and the migration's `NOT NULL` tightening from Section 11 happens then), Phase 8G (enabling/verifying RLS against real users), Phase 8H (full multi-user end-to-end verification).

## 24. Manual Instructions for Applying the SQL Migration

The migration was **not** executed automatically by this phase. To apply it:

1. Locate the file: `supabase/migrations/20260914120000_create_procurement_runs.sql`.
2. **Option A — Supabase Dashboard SQL Editor:** open your Supabase project → SQL Editor → paste the full contents of the file → Run. The statements are idempotent (`IF NOT EXISTS`) and contain no destructive operation, so this is safe even if run more than once.
3. **Option B — Supabase CLI (official migration workflow):** if you have the Supabase CLI linked to this project, the file is already named in the CLI's expected `supabase/migrations/<timestamp>_<description>.sql` format and can be applied via the CLI's standard migration-push command for your CLI version.
4. After applying, confirm the table exists (e.g., `select * from procurement_runs limit 1;` in the SQL Editor — should return zero rows, no error).
5. To actually route the running backend at this table, set `DATABASE_URL` in `backend/.env` (copy from `backend/.env.example`) to your project's Postgres connection string — never commit this file.

No credentials are included in this report, and none were requested from the user during this phase.

---

**Files/reports read for this phase:** `reports/phase8a_supabase_multiuser_architecture.md`, `reports/phase8a_architecture_decision_record.md`, `reports/phase8a_migration_roadmap.md`, `backend/persistence/database.py`, `backend/persistence/repository.py` (pre-Phase-8B), `backend/api/dependencies.py`, `backend/api/routes/procurement.py`, `backend/api/main.py`, `backend/api/schemas.py`, `tests/persistence/test_repository.py`, `tests/api/conftest.py`, `requirements.txt`, `.gitignore`.
**Files created:** see Section 19. **Files modified:** see Section 20.
