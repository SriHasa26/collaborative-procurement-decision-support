# Phase 8A — Migration Roadmap

**Date:** 2026-09-14
**Scope:** Testing strategy (Step 17), migration risks (Step 18), and the proposed Phase 8B–8H implementation roadmap (Step 19). Companion to `phase8a_supabase_multiuser_architecture.md` and `phase8a_architecture_decision_record.md`. Design only — nothing here has been implemented.

---

## 1. Testing Strategy (Design Only)

### Authentication / cross-user isolation tests (the critical security suite)

| # | Scenario | Expected result |
|---|---|---|
| 1 | Unauthenticated request to a protected endpoint | `401 Unauthorized` |
| 2 | Request with an invalid/malformed/expired token | `401 Unauthorized`, generic message (Section 8 of the architecture report) |
| 3 | Request with a valid token | Proceeds normally |
| 4 | User A submits an analysis | A row is created with `user_id = A` |
| 5 | User B submits an analysis | A row is created with `user_id = B`, independent of A's |
| 6 | User A lists history (`GET /procurement/runs`) | Only User A's runs are returned — User B's run is **absent**, not merely unselected |
| 7 | User B lists history | Only User B's runs are returned |
| 8 | User A requests User B's specific `run_id` | **`404 Not Found`** (Section 8's information-leak reasoning — never 403, never the actual data) |
| 9 | User A requests their own `run_id` | Full stored result returned, matching what was originally computed |

This suite directly encodes the required security property ("User A must not access User B's run") as executable tests, to be written once the local-JWT-verification mechanism (ADR-4) exists — using **locally-generated test tokens**, not a live Supabase project, preserving the existing test suite's offline property (see ADR-4's testability reasoning).

### Database / RLS tests

- Verify `SELECT`/`INSERT` policies behave as designed when queried **as** a given user (e.g., via Supabase's own local testing tools, or a test harness that sets the appropriate session role/claims) — independent of and in addition to the application-level tests above, since RLS is a second, independent enforcement layer (ADR-5) and must be verified as such, not assumed correct because the application-level tests pass.
- Verify no `UPDATE`/`DELETE` policy exists (i.e., those operations are correctly refused for everyone) — a negative test, matching ADR-6's "no such operation exists" decision.

### Frontend protected-route tests

- Visiting a protected route while unauthenticated redirects to `/login`.
- Visiting a protected route while authenticated renders the intended page.
- Logging out from a protected route redirects away and prevents returning via back-navigation without re-authenticating.
- Session restoration on page reload (an already-logged-in user reloading the tab remains logged in, without a visible flash of the login page).

None of the above tests are written in this phase — they are designed here so the implementation phases (8C–8H) have a concrete, agreed target to build against and verify, in the same spirit as this project's existing "real integration verification" standard (Phase 6H, Phase 7G).

## 2. Migration Risks and Mitigations

| Risk | Mitigation |
|---|---|
| **Breaking existing API contracts** (response shapes the frontend depends on) | `ProcurementRunResult`/`RunSummary`/`StoredRun` shapes stay identical; only *how* a request is authorized and *where* data is stored changes. Verified by re-running the exact Phase 7G real-browser end-to-end journey against the new backend before considering any phase complete. |
| **Breaking the existing 122-test backend suite** | The decision engine (`backend/core/`, `backend/services/`, `backend/models/`) is untouched by this entire migration (Section 2 of the architecture report) — those tests have no auth/database dependency today and should need zero changes. Persistence-layer tests will need new, *additional* Postgres-backed equivalents, not replacements of the existing SQLite ones, until SQLite is actually retired. |
| **Duplicating persistence logic** (e.g., writing similar-but-subtly-different SQL twice) | Formalize the repository interface first (ADR-7) so both implementations are verified against the *same* documented contract, ideally the same shared test suite parametrized over both backends. |
| **Trusting a frontend-supplied `user_id`** | Structurally prevented by ADR-3 — `ProcurementAnalysisRequest` never gains a `user_id` field; code review of every new/changed route handler should explicitly check this. |
| **Leaking the Supabase service-role key** | Never placed in any `VITE_`-prefixed variable or any frontend-shipped file (Section 13 of the architecture report); a pre-commit/code-review checklist item for Phase 8B onward. |
| **Incorrect or missing RLS policies** | RLS is explicitly *not* the sole enforcement layer (ADR-5) — a bug here is caught by the application-level `WHERE user_id` checks first; RLS-specific tests (Section 1 above) verify it independently rather than assuming it's correct because the app-level tests pass. |
| **Auth/database mismatch** (a user exists in Supabase Auth but their rows reference a stale/incorrect `user_id`, or vice versa) | The `user_id` foreign key (`REFERENCES auth.users(id)`) makes this a database-enforced constraint, not just a convention — an orphaned/mismatched `user_id` is rejected at insert time by Postgres itself. |
| **Test suite becoming dependent on a live external service** | Explicitly avoided by ADR-4's local-JWT-verification choice — auth tests use locally-generated tokens, not a live Supabase call. |
| **Silent data loss during the SQLite→Postgres transition** | ADR-7 explicitly keeps the existing SQLite file untouched during the swap; any carrying-forward of historical rows is a separate, explicit, reviewed step — never an automatic or silent one. |

## 3. Phase 8 Implementation Roadmap

The prompt's suggested 8B–8H structure was evaluated against the actual dependency graph uncovered during inspection (Section 2 of the architecture report) and found sound, with scope clarifications noted per phase below. One adjustment: **8C (frontend auth UI) and 8D (backend JWT verification) have no hard dependency on each other** — either could be built first, or in parallel — but are kept in this sequence for narrative clarity and because testing 8D end-to-end benefits from 8C already existing to produce a real token; this flexibility is called out explicitly rather than presented as a rigid requirement.

| Phase | Scope | Depends on | Testable exit criterion |
|---|---|---|---|
| **8A** | Architecture design (this phase) | — | Three design documents exist; no code changed |
| **8B** | Create the actual Supabase project; establish frontend/backend environment variable *placeholders* (names only, per Section 14 of the architecture report); no application code changes | 8A | Supabase project exists; env var scaffolding documented |
| **8C** | Supabase Authentication in the frontend: `AuthContext`, `/login`, `/signup`, `ProtectedRoute`, session restoration, logout | 8B | A user can sign up, log in, see a protected page, log out, and reload without losing session — verified against Supabase directly, no FastAPI involvement yet |
| **8D** | FastAPI JWT verification: a new auth dependency verifies the bearer token and extracts `user_id`, applied to the existing endpoints per Section 8's access table — initially provable via a minimal endpoint before wiring into real persistence | 8B (can proceed in parallel with 8C) | Unauthenticated/invalid/valid-token requests behave per Section 8's HTTP table, tested with locally-generated tokens (ADR-4) |
| **8E** | PostgreSQL persistence migration: formalize the repository interface (Section 10), implement the Postgres-backed version, create the schema (Section 6), swap it behind the existing `get_repository()` seam | 8B, informed by 8D's `user_id` availability | Existing API behavior reproduced against Postgres instead of SQLite; persistence tests pass against the new backend |
| **8F** | Wire the verified `user_id` (from 8D) into the real route handlers' calls to the 8E repository — the "glue" step connecting authentication to ownership | 8D, 8E | A logged-in user's runs are saved with their own `user_id` and retrievable only by them, in the real running system |
| **8G** | Row Level Security policies (Section 7) enabled on the live table; the full cross-user security test suite (Section 1 above) executed | 8E, 8F | User A cannot access User B's run under any tested path (application-level *and* RLS-level) |
| **8H** | End-to-end multi-user verification: two real user accounts, full real-browser journey per user, mirroring Phase 7G's own verification rigor | 8C–8G complete | Two independent users can each use the complete application without any visibility into each other's data, verified in a real browser against the real, fully-migrated system |

Each phase above has a single, narrow concern, a clear predecessor, and a concrete, testable exit condition — no phase mixes authentication, persistence, and security-policy work together, per this phase's own instruction to avoid mixing multiple major concerns per phase.

---

**Files created:** this report (plus the two companion documents). **Files modified:** none.
