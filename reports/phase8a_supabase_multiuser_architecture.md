# Phase 8A — Supabase & Multi-User Architecture Design

**Date:** 2026-09-14
**Scope:** Architecture and migration design only. No code was written or modified. This document covers Steps 1–16 of the Phase 8A brief; Steps 17–20 are in the companion documents `phase8a_migration_roadmap.md` and `phase8a_architecture_decision_record.md`.

---

## 1. Purpose

The system currently supports exactly one, anonymous, unauthenticated user of the API — every procurement run is visible to anyone who can reach the backend. Phase 8's goal is multi-user support: real accounts, private per-user history, and cloud persistence, via Supabase (Authentication + PostgreSQL + Row Level Security). Phase 8A designs *how* this should work before any of it is built. The existing decision engine and its mathematics are explicitly out of scope and must remain untouched and independent of whatever auth/database technology sits around it.

## 2. Current Architecture Audit

Inspected directly: `backend/api/`, `backend/persistence/`, `backend/services/`, `backend/models/`, `frontend/src/api/`, `frontend/src/config/`, `frontend/src/pages/`, `frontend/src/components/`, `requirements.txt`, and the Phase 6F–7G reports (see file list at the end of this document — several report filenames in this phase's own instructions did not exactly match the actual files on disk, e.g. `phase7d_backend_submission_and_results_handoff.md`/`phase7f_run_history.md` vs. the real `phase7d_frontend_backend_analysis_integration.md`/`phase7f_run_history_and_detail_integration.md`; the actual files were located and read).

**A. Where SQLite is initialized:** `backend/persistence/database.py` — `initialize_database()` creates `data/app/procurement.db` and the `procurement_runs` table (`CREATE TABLE IF NOT EXISTS`) if missing; `get_connection()` opens one short-lived connection per call. `DEFAULT_DB_PATH = Path("data/app/procurement.db")`.

**B. Where procurement runs are persisted:** `backend/persistence/repository.py`'s `ProcurementRunRepository.save_run(run_input, run_result)` — called exactly once, from `backend/api/routes/procurement.py`'s `analyze_procurement` handler, **after** `ProcurementRunService().run(...)` has already produced the result (persistence is a side effect of a completed analysis, never a precondition for it).

**C. Where run history is retrieved:** `ProcurementRunRepository.list_runs()` → `GET /procurement/runs` route → returns an array of `RunSummary` (`run_id`, `created_at`, `commodity`, `run_status` only — deliberately lightweight, no counts, no JSON).

**D. Where run detail is retrieved:** `ProcurementRunRepository.get_run(run_id)` → `GET /procurement/runs/{run_id}` route → returns `StoredRun` (`run_id`, `created_at`, `commodity`, `run_status`, `input`, `result`), where `.result` is the exact same `ProcurementRunResult` shape `POST /procurement/analyze` itself returns.

**E. How the frontend communicates with FastAPI:** `frontend/src/api/client.js` is the sole `fetch()` call site (enforced by convention since Phase 7A); `frontend/src/api/procurementApi.js` wraps it into four named functions (`healthCheck`, `analyzeProcurement`, `getProcurementRuns`, `getProcurementRun`); the base URL comes from `frontend/src/config/env.js`'s `VITE_API_BASE_URL`. CORS (`backend/api/main.py`, Phase 7A) is restricted to the local Vite dev origins only.

**F. Whether current API endpoints expose data without authentication:** **Yes — all four endpoints are completely public.** `GET /procurement/runs` returns every row in the table to any caller; `GET /procurement/runs/{run_id}` returns any run by ID to any caller. There is no concept of "owner" anywhere in the schema or the code today.

**G. Components that must remain unchanged / independent of Supabase, authentication, or the database implementation:**

| Layer | Files | Why it must stay independent |
|---|---|---|
| Core math | `backend/core/geo_math.py`, `decision_math.py` | Pure functions; already have zero I/O, zero framework awareness |
| Decision services | `backend/services/{demand_estimation,validation,eligibility,compatibility,group_formation,decision_engine,decision_evaluation,selection,batch_decision,pipeline}.py` | Operate on plain dataclasses in, plain dataclasses out — no database, no HTTP, no auth concept anywhere in this layer today, by original Phase 6A–6D design |
| Orchestration | `backend/services/procurement_run.py` (`ProcurementRunService`) | Sequences the above; already has no persistence or auth awareness (Phase 6E's own explicit design) |
| Data contracts | `backend/models/{contracts,enums,reasons,batch_contracts,group_formation_contracts,decision_contracts,run_contracts}.py` | Describe the math/decision domain only; `ProcurementRunResult` itself needs **no** `user_id` field — ownership is persistence-layer metadata, not a property of a computed decision |

This independence already exists by design (documented repeatedly across the Phase 6 reports) and is the reason Phase 8's changes can be scoped almost entirely to `backend/api/` and `backend/persistence/` plus new frontend auth code — not to any of the above.

## 3. Target Architecture Design

Recommended architecture (validated against alternatives below):

```
React Frontend
    │  (Supabase JS client, auth only)
    ▼
Supabase Authentication  ──issues──▶  JWT (access + refresh token)
    │
    │  every FastAPI request carries: Authorization: Bearer <JWT>
    ▼
frontend/src/api/client.js  (UNCHANGED as the sole fetch() site)
    ▼
FastAPI Backend
    │  1. verify JWT signature locally (JWKS) → extract verified user_id
    │  2. build ProcurementRunInput exactly as today (build_run_input) -- UNCHANGED
    ▼
Decision Engine (backend/core/, backend/services/) -- COMPLETELY UNCHANGED, no auth/user concept enters this layer
    ▼
Repository layer (backend/persistence/) -- interface unchanged in shape, new Postgres implementation
    │  explicit `WHERE user_id = :verified_user_id` on every query (application-level enforcement)
    ▼
Supabase PostgreSQL  -- RLS also enabled (defense-in-depth, Section 7)
```

**Alternative considered and rejected:** letting the frontend talk to Supabase's auto-generated PostgREST API directly for procurement-run data (bypassing FastAPI for reads), relying solely on RLS. Rejected because it would split the "who can see procurement data" question between two independently-evolving codebases (FastAPI's route logic and Postgres policies) and would let the frontend read `result_json` blobs whose *shape* is entirely owned by the Python decision engine's dataclasses — any future field change would require coordinating a raw SQL/PostgREST consumer, defeating the whole point of `backend/api/serialization.py`'s existing "one place that knows how to turn these contracts into JSON" design (Phase 6G). FastAPI remains the **only** thing that talks to the database, exactly as today, just now on a different database engine.

**Responsibilities:**
- **Frontend:** obtains and refreshes the user's session via Supabase's JS client; attaches the resulting token to every FastAPI request; renders login/signup/protected routes. Never talks to Postgres or Supabase's data API directly.
- **Supabase (Auth):** owns user identity, password/session management, JWT issuance and signing.
- **Supabase (Postgres):** stores `procurement_runs` (now with `user_id`); enforces RLS as a second, independent layer of protection.
- **FastAPI:** unchanged orchestration role, plus one new responsibility — verify the caller's JWT and use the verified `user_id` for every persistence call. Still the sole component that opens a database connection.
- **Decision Engine:** completely unaware any of this exists — same pure input-in/result-out contract as today.

## 4. Authentication Flow Design

```
                     ┌─────────────────────────────────────────────┐
                     │                React Frontend                │
                     │                                               │
  Sign up/Login ───▶ │  Supabase JS client (supabase-js)             │
                     │      │ signUp() / signInWithPassword()        │
                     │      ▼                                        │
                     │  Supabase Auth service  ──▶ JWT (access +      │
                     │      │                        refresh token)  │
                     │      ▼                                        │
                     │  Session stored & auto-refreshed              │
                     │  by the Supabase JS client itself              │
                     │      │                                        │
                     │      ▼                                        │
                     │  AuthContext (React) exposes {user, session}  │
                     │      │                                        │
                     │      ▼                                        │
                     │  client.js attaches                            │
                     │  "Authorization: Bearer <access_token>"        │
                     └───────────────────┬───────────────────────────┘
                                          ▼
                                   FastAPI Backend
                          verify JWT (local, via JWKS) → user_id
                                          ▼
                              existing pipeline, unchanged
```

- **Sign up / Login:** the Supabase JS client's own `signUp()`/`signInWithPassword()` calls talk directly to Supabase Auth — FastAPI is not involved in credential handling at all (it never sees a password).
- **Logout:** `signOut()` clears the local session; `AuthContext` updates; protected routes redirect to `/login`.
- **Session persistence:** handled by the Supabase JS client's own storage mechanism (browser storage) and restored automatically on app load.
- **Token refresh:** handled automatically by the Supabase JS client before expiry — the frontend never manually manages refresh logic.
- **Authenticated API requests:** every call through `client.js` attaches the current access token as a bearer header.
- **FastAPI verification:** a new dependency validates the JWT's signature and expiry (Section 16) and extracts the verified `sub` claim as the request's `user_id` — this is the **only** source of user identity FastAPI ever trusts (Section 5).

## 5. User Data Ownership Model

```
auth.users (owned by Supabase Auth)
        │ 1
        │
        │ owns
        │
        │ many
        ▼
procurement_runs.user_id  (new column, foreign key → auth.users.id)
```

`procurement_runs` needs a `user_id` column. **Its value must come exclusively from the verified JWT FastAPI itself decodes on the server side — never from any field in the request body JSON.** `ProcurementAnalysisRequest` (`backend/api/schemas.py`) must **not** grow a `user_id` field; if a client-supplied `user_id` were ever accepted and trusted, any caller could read or write another user's data simply by editing a JSON field before sending it — a textbook Insecure Direct Object Reference (IDOR) vulnerability, and it would also contradict the very reason Supabase Auth is being introduced. The route handler's shape becomes conceptually: `verified_user_id = get_current_user(request)` (new, from the JWT) → `repository.save_run(user_id=verified_user_id, run_input=..., run_result=...)` — the payload's *content* is exactly what it is today; only the *ownership* is added, server-side, out of band from the request body.

## 6. Database Migration Design

**Recommendation: keep the existing single-table, JSON-column design, and add `user_id`.** Do not normalize `input_json`/`result_json` into relational columns. Reasoning, evaluated against the stated criteria, not for "academic appearance":

- **Current project requirements / query requirements:** the only query patterns that exist today are "list a user's runs, newest first" (metadata only) and "fetch one run's complete input+result by ID" — both already satisfied by the existing shape plus a `user_id` filter. No requirement has ever emerged to query *inside* the JSON (e.g., "find all runs with savings above X").
- **Traceability:** the JSON blob is an intentional, immutable snapshot of exactly what the decision engine computed (Phase 6G's own original design rationale) — decomposing it into relational columns would require a second schema that must be kept in lock-step with the Python dataclasses' own evolution (`ProcurementRunResult`, `EvaluatedGroupResult`, etc.), a real drift risk for no current benefit.
- **Simplicity / security:** RLS operates on the row's `user_id` column; it is completely indifferent to what's inside the JSON columns. Normalizing would not improve security at all.
- **Future extensibility:** Postgres's native `JSONB` type (an upgrade from SQLite's plain `TEXT`) still permits *optional* future querying into the JSON (`->>` operators, GIN indexes) if a real need ever appears — without committing to normalization now.

**Recommended schema:**
```sql
CREATE TABLE procurement_runs (
    run_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    commodity               TEXT NOT NULL,
    run_status              TEXT NOT NULL,
    eligible_vendor_count   INTEGER NOT NULL,
    candidate_group_count   INTEGER NOT NULL,
    selected_group_count    INTEGER NOT NULL,
    input_json              JSONB NOT NULL,
    result_json             JSONB NOT NULL
);

CREATE INDEX idx_procurement_runs_user_created
    ON procurement_runs (user_id, created_at DESC);
```
- **Primary key:** `run_id` (UUID — the existing Python-side `uuid.uuid4()` generation in `repository.py` can continue to supply it, or Postgres's own `gen_random_uuid()` default can take over; either is compatible with the existing shape).
- **Foreign key:** `user_id → auth.users(id)`. `ON DELETE CASCADE` is proposed as the default (a deleted account's runs are deleted with it) — flagged explicitly as a product decision to confirm with the user before implementation, not decided unilaterally here.
- **Data types:** `TEXT`→`JSONB` for the two JSON columns (Postgres-native, indexable if ever needed); `TEXT`→`TIMESTAMPTZ` for `created_at` (proper temporal type; the existing code already stores UTC ISO-8601 strings, so this is a natural, compatible upgrade, not a behavior change).
- **Index:** a composite `(user_id, created_at DESC)` index directly matches `repository.py`'s existing `list_runs()` query pattern (`ORDER BY created_at DESC, run_id DESC`), now additionally filtered by owner.

## 7. Row Level Security Design

Required property: a user must only be able to access their own `procurement_runs` rows.

| Operation | Needed? (per actual repository.py methods) | Policy design |
|---|---|---|
| SELECT | Yes (`list_runs`, `get_run`) | `USING (auth.uid() = user_id)` |
| INSERT | Yes (`save_run`) | `WITH CHECK (auth.uid() = user_id)` — prevents a row being inserted claiming another user's ownership |
| UPDATE | **No** | No code path modifies a stored run after creation — runs are immutable snapshots (Phase 6G's own explicit design: "the database is a persistence snapshot... must not reinterpret or recompute the result"). No UPDATE policy is proposed; inventing one would be unrequested CRUD. |
| DELETE | **No, not currently** | No delete endpoint exists today. If a future phase adds "delete my run history," the policy would be `USING (auth.uid() = user_id)`, symmetric with SELECT — noted here only as a future extension point, not designed further now. |

**How RLS protects against cross-user access:** even if FastAPI's own application-level `WHERE user_id = ...` filtering (Section 3/9) ever had a bug — a forgotten clause, a copy-paste error in a new endpoint, a future direct-from-frontend access path via Supabase's own auto-generated data API — Postgres itself refuses to return or accept rows that fail the policy, at the database engine level, independent of any application code. This is why RLS is recommended as **defense-in-depth** alongside explicit filtering, not as a replacement for it (see ADR-5 in the companion decision record).

## 8. API Security Design

| Endpoint | Access level | Reason |
|---|---|---|
| `GET /health` | **Public** | A liveness probe with no user data; must be reachable without credentials for monitoring |
| `POST /procurement/analyze` | **Authenticated** | Creates a row owned by the caller — the caller's identity must be known |
| `GET /procurement/runs` | **Authenticated** | Must return only the caller's own rows, never the full table |
| `GET /procurement/runs/{run_id}` | **Authenticated + ownership check** | Must verify the specific run belongs to the caller, not merely that *some* valid user is calling |

**Recommended HTTP behavior:**
- **Missing authentication** (no `Authorization` header): `401 Unauthorized`.
- **Invalid/expired/malformed token:** `401 Unauthorized`, with a single generic message ("invalid or missing authentication") — deliberately not distinguishing "expired" from "malformed" in the response, to avoid giving an attacker a useful signal about *why* a token failed.
- **Valid authentication:** proceed exactly as today for the caller's own data.
- **Attempting to access another user's run** (valid token, but `run_id` belongs to someone else): **`404 Not Found`, not `403 Forbidden`.** Returning 403 would confirm to the caller that the `run_id` exists at all, just isn't theirs — an information leak (a standard OWASP concern for object-level authorization). Returning 404 makes "doesn't exist" and "exists but isn't yours" indistinguishable from outside, and — usefully — this falls out **for free** from the design in Section 3/7: if `get_run` always filters by `WHERE run_id = :id AND user_id = :verified_id`, a foreign run simply isn't found by the query; no separate "check ownership, then decide 403 vs 200" branch is needed.

## 9. SQLite Migration Strategy

The current SQLite implementation works correctly and is not being deleted blindly. Options evaluated:

| Option | Evaluation |
|---|---|
| A. Keep SQLite temporarily | Doesn't advance the actual goal — SQLite has no multi-tenant/auth integration or RLS concept; keeping it doesn't unblock multi-user support |
| B. Dual persistence (write to both simultaneously) | Adds real complexity (two sources of truth, drift risk) for a benefit (zero-downtime live cutover) this project doesn't need — there is no live production deployment with active users today (Phase 7 reports describe a local-dev project only) |
| **C. Replace the repository behind its existing interface** | **Recommended.** `repository.py`'s own docstring already states it is "the only component in this project allowed to open a SQL connection," and it is already injected via `backend/api/dependencies.py`'s `get_repository()` — a clean seam Phase 6G/6H already built for exactly this kind of swap. Low risk, incremental, testable in isolation. |
| D. Full replacement with no interface | Higher risk, harder to test incrementally, and ignores the seam the codebase already provides for free |

**Recommendation: Option C.** Formalize `ProcurementRunRepository`'s three-method shape (`save_run`/`get_run`/`list_runs`, now each accepting a `user_id`) as an explicit interface (Section 10), implement a new Postgres-backed version, and swap it behind the existing `get_repository()` dependency-injection point — no change needed to the route handlers' call sites beyond passing the now-available verified `user_id` through.

**What must be preserved regardless of which option is chosen:**
- **Existing API response shapes** — `ProcurementRunResult`, `RunSummary`, `StoredRun` stay byte-for-byte identical to the frontend; only the storage engine changes, never the contract.
- **Decision engine independence** — this migration touches only `backend/persistence/` (and, for auth, `backend/api/`); `backend/core/`, `backend/services/`, and `backend/models/`'s business contracts are untouched.
- **Testability** — `tests/persistence/test_repository.py`'s existing pattern (an isolated, `tmp_path`-based database per test) needs a Postgres-compatible equivalent designed in the implementation phase (e.g., a dedicated ephemeral test schema/database) — not designed further here, flagged as a concrete task for Phase 8E.
- **Existing data integrity** — the current `data/app/procurement.db` file is not touched by this phase, and no future phase should touch it silently; if the existing local rows are ever worth carrying forward, that would be one explicit, reviewed, opt-in migration script — a decision to make *with* the user when that phase is reached, not assumed here.

## 10. Repository Abstraction Analysis

`ProcurementRunRepository` (`backend/persistence/repository.py`) is not currently behind a formal interface (no `Protocol`/ABC) — but it is already well-isolated in practice: it is the sole SQL-connection owner, it is already dependency-injected (`backend/api/dependencies.py`), and callers only ever use its three public methods with clearly-typed inputs/outputs (`RunSummary`, `StoredRun`). A formal interface would make that implicit contract explicit.

| | Assessment |
|---|---|
| **Pros** | Enables swapping the concrete class behind the *same* `get_repository()` seam with zero change to route handlers; enables running the same test suite against both a SQLite and a Postgres implementation to verify behavioral equivalence; documents the exact contract explicitly |
| **Cons** | One more abstraction layer for what is, today, a single implementation — normally a case for "premature abstraction" under this project's own stated ethos, **except** that a second, real implementation (Postgres) is now genuinely imminent, which is exactly when extracting an interface stops being premature; the three method signatures need a small, real addition (`user_id` threaded through all three) |
| **Migration impact** | Low if done as Option C (Section 9) — route handlers already call through the injected instance; only the DI wiring and the new `user_id` parameter change, not the call sites' overall shape |

No interface class is created in this phase — this section documents the recommendation for the implementation phase (Phase 8E).

## 11. Frontend Auth Architecture

**New pages (design only):** `/login`, `/signup` (public). Existing pages (`/analyze`, `/results`, `/history`) become protected (require an active session). `/` (Home) is flagged as an **open product question** rather than decided here: it could remain public (a marketing/info page with a "Sign In" call to action) or become protected immediately — noted for explicit confirmation in Phase 8C, not assumed.

**Where auth state should live:** a **React `Context`** (`AuthContext`, exposing `{ user, session, signIn, signUp, signOut, loading }`), provided once at the top of the tree (in `App.jsx`, alongside `BrowserRouter`). This follows directly from the project's own existing, explicit rule against introducing Redux/Zustand: Context is the right tool specifically *because* auth state is needed by many unrelated parts of the tree (route guards, a future user indicator in `Sidebar`, the API client's token-attachment logic) — the canonical case Context exists for — whereas the existing form/history state (Phase 7C/7F) correctly stayed local precisely because it was *not* needed elsewhere. Prop-drilling was considered and rejected for the same reason; a third-party auth-context library (e.g. `@supabase/auth-helpers-react`) was considered and rejected as an unnecessary dependency beyond the Supabase JS client itself.

**Route protection design:** a `ProtectedRoute` wrapper (read `AuthContext`; render children if `user` is present; otherwise `<Navigate to="/login">`), applied inside `AppRoutes.jsx` around the routes that need it — the existing route table structure (a shared `AppLayout` wrapping child routes, Phase 7B) already has the right shape to nest a second protective layer without restructuring it.

**Session restoration:** on mount, `AuthContext`'s provider calls Supabase's session-restore API once (mirroring the exact "fetch on mount via one effect" pattern `HistoryPage.jsx` already established in Phase 7F, for consistency), showing a brief loading state until the initial check resolves — avoiding a flash-of-redirect-to-login before an existing session is confirmed.

**Logout behavior:** call Supabase's sign-out, clear local context state, redirect to `/login` (or Home, depending on the Section-11 open question above).

**Unauthenticated redirects:** a protected route visited without a session redirects to `/login`; the originally-requested path can be preserved via the *same* `react-router-dom` navigation-state mechanism already used for the analysis-result handoff (Phase 7D `navigate(path, { state })`) so the user returns to where they were after logging in — reusing an existing pattern, not inventing a new one.

## 12. API Client Auth Design

`frontend/src/api/client.js` remains the **sole** `fetch()` location — this principle is preserved, not touched, by this design. The planned (not-yet-implemented) change: `request()` would attach `Authorization: Bearer <access_token>` to the same `headers` object it already builds alongside the existing `Content-Type: application/json`.

Two ways to let `client.js` (a plain module, not a React component) obtain "the current token" were considered:
- **(a) `client.js` imports the Supabase JS client directly** and reads the current session itself before each request.
- **(b) `AuthContext` pushes a token-getter into `client.js`** once at app startup, keeping `client.js` free of any Supabase SDK import.

**Recommendation: (a).** It keeps `client.js` fully self-sufficient, extending its own existing stated role ("the ONLY module in the frontend that calls fetch directly") to naturally include "and reads the current session," with no cross-module wiring needed at startup. This is a recommendation for the implementation phase — no code is written here.

## 13. Supabase Security Architecture

| Key | May appear in frontend env vars? | Why |
|---|---|---|
| **anon (public) key** | **Yes** — `VITE_SUPABASE_ANON_KEY` | Designed to be public; identifies the *project*, not a privileged caller; every request made with it is still fully subject to RLS — it has no bypass power, exactly analogous to a Stripe publishable key |
| **service_role key** | **Never, under any circumstances** | Bypasses RLS entirely — full read/write access to every row of every user. Since Vite bundles every `VITE_`-prefixed variable directly into the shipped browser JS (the exact mechanism `frontend/src/config/env.js` already relies on for `VITE_API_BASE_URL`, Phase 7A), **nothing** with that prefix can ever hold a secret — this is a hard constraint of the build tool itself, not a preference. The service_role key belongs only in FastAPI's own server-side environment. |

## 14. Environment Configuration Plan

No values are invented — names and responsibilities only.

**Frontend (`frontend/.env`, extending the existing Phase 7A pattern):**
| Variable | Responsibility |
|---|---|
| `VITE_API_BASE_URL` | *(existing, unchanged)* FastAPI base URL |
| `VITE_SUPABASE_URL` | Supabase project API URL — safe to expose |
| `VITE_SUPABASE_ANON_KEY` | Supabase public anon key — safe to expose (Section 13) |

**Backend (new — FastAPI currently has zero environment variables):**
| Variable | Responsibility |
|---|---|
| `SUPABASE_URL` | Same project URL, used server-side for JWKS/JWT verification |
| `SUPABASE_JWT_SECRET` or JWKS endpoint configuration | Used to verify incoming JWT signatures (exact form depends on Section 16's implementation) — server-side only |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side only, never logged or returned in any response — used only where FastAPI genuinely needs elevated database access |
| `DATABASE_URL` | Postgres connection string (if FastAPI connects directly rather than through a client library) — server-side only, contains embedded credentials |

## 15. Data Privacy Analysis

**Data minimization:** Supabase Auth needs only what it already requires for the chosen sign-in method (e.g., email + password) — no additional profile fields (real name, phone, address) are needed for this project's scope, and none should be added merely because accounts now exist. **User ownership:** multi-user support changes *who* owns/sees a procurement run; it does not change *what* is collected about vendors within a run. **Vendor data:** remains exactly as minimal as Phases 5–7C already established — `vendor_id` is an arbitrary string the submitting user chooses, not a verified identity; no vendor personal-identity data (real name, phone, physical address) is introduced by this architecture, and none should be, as a side effect of adding user accounts. **Approximate location handling:** unchanged — `VendorLocationStatus` (`VENDOR_SPECIFIC_APPROXIMATE` / `LOCALITY_CENTROID_PROXY` / `MISSING`) is a vendor-location-precision concept, entirely unrelated to *run* ownership, and must not be conflated with or "improved" as an incidental side effect of this work.

## 16. Backend Auth Verification Strategy

| Option | Assessment |
|---|---|
| A. Local JWT verification (verify signature locally using Supabase's cached JWKS) | Fast (no network call per request), no per-request availability dependency on Supabase, industry-standard for JWT-based auth, and — critically for this project — **testable without any live external service** |
| B. Call Supabase's verification endpoint on every request | Adds latency and an external dependency to *every* API call (not just login), and makes the backend's own availability depend on Supabase's auth service being reachable for every request; no real security advantage over A, since both ultimately trust the same signing key |
| C. JWKS-based verification | The specific mechanism Option A uses to obtain/rotate the public signing key over time — not a distinct alternative, described together with A |

**Recommendation: A/C — local JWT verification via a cached JWKS.** Justified by:
- **Security:** identical guarantee to calling Supabase per-request (same cryptographic signature check), just performed locally.
- **Simplicity:** one small, well-scoped verification dependency added to `backend/api/`, using a well-maintained JWT library.
- **Project scope:** avoids adding an external network call to the hot path of every request, appropriate for this project's current scale.
- **Testability:** local verification can be exercised in `pytest` using locally-generated test tokens signed with a test key, with **zero dependency on a real, reachable Supabase project during test runs** — directly preserving the existing test suite's current property of being fully offline (122 tests, no network access today). Option B would break this property for every future auth-related test.

---

**Files/reports read for this phase:** `backend/api/main.py`, `backend/api/routes/procurement.py`, `backend/api/schemas.py`, `backend/api/serialization.py`, `backend/api/dependencies.py`, `backend/persistence/database.py`, `backend/persistence/repository.py`, `backend/services/*`, `backend/models/*`, `requirements.txt`, `frontend/src/api/client.js`, `frontend/src/api/procurementApi.js`, `frontend/src/config/env.js`, `frontend/src/pages/*`, `frontend/src/components/**`, `frontend/src/routes/AppRoutes.jsx`, `frontend/src/App.jsx`, plus every `reports/phase6*.md` and `reports/phase7*.md` file (actual filenames as they exist on disk).
**Files created:** this report (plus the two companion documents). **Files modified:** none.
