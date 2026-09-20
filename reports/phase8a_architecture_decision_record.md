# Phase 8A — Architecture Decision Record

**Date:** 2026-09-14
**Status:** Proposed (design only — nothing in this record has been implemented). Companion to `phase8a_supabase_multiuser_architecture.md` and `phase8a_migration_roadmap.md`.

Each entry: Context → Options Considered → Decision → Reason → Trade-offs.

---

## ADR-1: Authentication Provider

**Context:** The system needs real user accounts, login/logout, and session management for multi-user support.

**Options considered:**
- Supabase Auth
- Firebase Auth
- A custom auth system rolled directly in FastAPI (password hashing + hand-issued JWTs)
- A dedicated auth-as-a-service provider (e.g. Auth0, Clerk)

**Decision:** Supabase Auth.

**Reason:** It is the provider explicitly being evaluated for this project, and — critically — it is bundled with the database choice (ADR-2): using Supabase for both auth and Postgres means `auth.uid()` is natively available inside Postgres Row Level Security policies (ADR-6) with no extra integration work, and avoids introducing a *third* external vendor (auth provider + database provider + hosting) when one provider can supply two of the three needs.

**Trade-offs:** Vendor lock-in to Supabase's specific JWT claim shape and auth API. Accepted, since the database is being paired with the same vendor anyway (ADR-2), and a custom-rolled auth system would mean re-implementing (and re-securing) password storage, session/refresh-token handling, and email flows this project has no current need to own.

---

## ADR-2: Database

**Context:** SQLite (Phase 6G) has no native multi-tenant or cloud-access story; multi-user support needs a database reachable by a hosted backend and, ideally, integrated with the chosen auth provider.

**Options considered:**
- Keep SQLite
- Self-hosted PostgreSQL (a VM/container the team manages)
- Supabase-hosted PostgreSQL (managed)

**Decision:** Supabase-hosted PostgreSQL.

**Reason:** Managed (no operational burden for a project of this scope), and gives native, first-class Row Level Security integration with Supabase Auth's `auth.uid()` (ADR-6) — the two products are designed together.

**Trade-offs:** A recurring hosting dependency and cost, versus SQLite's zero-cost, zero-ops simplicity. Accepted because multi-user support is the explicit, stated goal of Phase 8, and SQLite structurally cannot provide it.

---

## ADR-3: Source of User Identity for API Requests

**Context:** `procurement_runs` needs to know which user owns each row; the request payload (`ProcurementAnalysisRequest`) could theoretically carry a `user_id` field directly.

**Options considered:**
- Accept and trust a `user_id` field supplied in the request JSON
- Derive `user_id` exclusively from a verified JWT, server-side, never from the request body

**Decision:** Derive from a verified JWT only. `ProcurementAnalysisRequest` gains **no** `user_id` field.

**Reason:** Trusting a client-supplied identity field is a textbook Insecure Direct Object Reference (IDOR) vulnerability — any caller could read or write another user's data by editing one JSON field. This is a hard security requirement, not a design preference.

**Trade-offs:** None of substance — this is strictly safer with no functional downside; the payload's actual *content* is unchanged from today, only *ownership* is added out-of-band.

---

## ADR-4: FastAPI JWT Verification Method

**Context:** FastAPI must confirm that an incoming `Authorization: Bearer <token>` header is a genuine, unexpired Supabase-issued token before trusting its claims.

**Options considered:**
- Local signature verification using Supabase's cached JWKS (public key set)
- Calling a Supabase verification endpoint on every incoming request
- (JWKS-based verification is the mechanism Option 1 uses, not a separate option)

**Decision:** Local JWT verification via a cached JWKS.

**Reason:** Identical cryptographic security guarantee to calling Supabase per-request, but with no added latency, no per-request external dependency, and — importantly — it can be fully exercised in `pytest` using locally-generated test tokens with zero dependency on a reachable, live Supabase project, preserving the project's current fully-offline test suite (122 tests today).

**Trade-offs:** Requires the backend to fetch and periodically refresh the JWKS (a small, standard, well-supported pattern in existing JWT libraries) rather than being a completely stateless per-call check — a negligible cost against the alternative's much larger latency/availability cost.

---

## ADR-5: Database Connection & Ownership Enforcement Model

**Context:** With Postgres RLS available, FastAPI could either (a) forward each user's own JWT so Postgres enforces ownership entirely via RLS, or (b) hold its own privileged server-side connection and filter explicitly in application code.

**Options considered:**
- (a) FastAPI forwards the caller's JWT to Supabase's client library/PostgREST for every query; RLS is the *sole* enforcement mechanism
- (b) FastAPI holds a privileged server-side connection, explicitly filters every query by the verified `user_id`, with RLS enabled as a second, independent layer
- (c) Application-level filtering only, no RLS

**Decision:** (b) — explicit application-level filtering as the primary mechanism, RLS enabled as defense-in-depth.

**Reason:** Keeps FastAPI as the single, consistent data-access point, matching the system's existing architecture exactly (the frontend has never talked to a database directly, only to FastAPI) — introducing per-request token-forwarding through an additional client library layer would be a new architectural pattern for no proportionate benefit at this project's scale. RLS is still enabled so that *any other* access path (e.g. if Supabase's own auto-generated data API were ever exposed by mistake, or a future admin tool connects directly) is independently protected at the database engine level, not just by application code discipline.

**Trade-offs:** FastAPI's own queries do not get *automatic* protection from RLS, since they use a privileged connection — this is explicitly mitigated by disciplined, code-reviewed, explicitly-tested `WHERE user_id = :verified_id` clauses in every repository method (Phase 8G's dedicated security testing, see roadmap). Option (a) was rejected specifically because it would have made RLS the *only* line of defense with no independent application-level check.

---

## ADR-6: Row Level Security Scope

**Context:** RLS policies must be designed for exactly the operations the system actually performs.

**Options considered:**
- Full CRUD policies (SELECT/INSERT/UPDATE/DELETE) "for completeness"
- Only the policies matching real, existing repository operations

**Decision:** SELECT and INSERT policies only, both scoped to `auth.uid() = user_id`. No UPDATE or DELETE policy.

**Reason:** `backend/persistence/repository.py` has exactly three operations today — `save_run` (INSERT), `get_run`/`list_runs` (SELECT) — and no code path ever modifies or removes a stored run (runs are immutable snapshots, an explicit Phase 6G design decision). Adding UPDATE/DELETE policies for operations that don't exist would be unrequested, speculative CRUD.

**Trade-offs:** None currently. If a future phase adds "delete my history," a symmetric `DELETE ... USING (auth.uid() = user_id)` policy would be added at that time, not preemptively now.

---

## ADR-7: SQLite → PostgreSQL Migration Strategy

**Context:** The working SQLite implementation must transition to Supabase PostgreSQL without breaking the existing API contract or losing decision-engine independence.

**Options considered:**
- A. Keep SQLite temporarily (no real progress toward the goal)
- B. Dual persistence (write to both simultaneously during a transition window)
- C. Replace the repository implementation behind its existing dependency-injection seam
- D. Full replacement with no interface abstraction

**Decision:** C.

**Reason:** `backend/persistence/repository.py` is already the sole SQL-connection owner and is already injected via `backend/api/dependencies.py`'s `get_repository()` — a clean seam Phase 6G/6H already built. Dual persistence (B) solves a zero-downtime-live-cutover problem this project doesn't have (there is no live production deployment with active users yet). Option A doesn't advance the goal at all.

**Trade-offs:** Requires formalizing the repository's implicit contract as an explicit interface first (ADR/Section 10 of the architecture report) — a small, low-risk, now-justified step since a second real implementation is imminent. The existing local `data/app/procurement.db` file is left in place, untouched, by this decision; whether/how to carry its historical rows forward into Postgres is an explicit, separate decision for the implementation phase, not assumed here.

---

## ADR-8: Schema Design (Normalized vs. JSON-Column)

**Context:** The existing `procurement_runs` table stores `input_json`/`result_json` as opaque blobs rather than normalized relational columns.

**Options considered:**
- Normalize `input_json`/`result_json` into multiple relational tables mirroring the decision engine's dataclasses
- Keep the single-table, JSON-column design (upgrading `TEXT` → `JSONB`), adding only `user_id`

**Decision:** Keep the single-table, JSON-column design; add `user_id UUID NOT NULL REFERENCES auth.users(id)` and a supporting `(user_id, created_at DESC)` index.

**Reason:** No current or anticipated query needs to filter/sort *inside* the JSON; the JSON blob is an intentional immutable snapshot (Phase 6G's own original rationale, still valid); normalizing would create a second schema that must track the Python decision-engine's dataclasses over time, a real drift risk for no demonstrated benefit; RLS is indifferent to what's inside JSON columns, so normalization buys nothing security-wise either.

**Trade-offs:** If a genuine future requirement emerges to query *inside* results (e.g., "show me all runs with savings over ₹X"), Postgres's `JSONB` operators/GIN indexes can address it without a schema rewrite — explicitly deferred, not designed now, since no such requirement exists today.

---

**Files created:** this report (plus the two companion documents). **Files modified:** none.
