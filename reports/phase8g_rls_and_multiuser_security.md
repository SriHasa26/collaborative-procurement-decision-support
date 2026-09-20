# Phase 8G — Real Supabase RLS and Multi-User Security Verification

**Date:** 2026-09-15

## 1. Objective

This phase verifies, with real evidence rather than code inspection alone:
- Supabase Row Level Security (RLS) actually enforces per-user isolation at the database layer.
- JWT identity propagation (`sub` → `current_user.user_id`) is unbroken.
- Application-level ownership filtering is correct and independent of RLS.
- Cross-user isolation holds at both the API layer and the direct-database layer.
- `user_id` cannot be spoofed from any client-controlled input.
- No secret (service-role key, database password, JWT, access/refresh token) is exposed in frontend code, built output, or logs.

## 2. Baseline

- Backend tests before this phase: **178 passed, 0 failed, 0 skipped** (re-run fresh at the start of this phase from the project root).
- Frontend build: **succeeds** (`npm run build`, one pre-existing bundle-size notice, not an error).
- Frontend lint: **clean, 0 warnings** (`npm run lint`).
- No file changes were pending from the prior (aborted) Phase 8G email-integration attempt — that attempt made zero code changes before being redirected to this phase.

## 3. Architecture Verified

```
Supabase Auth
     |
JWT (access_token)
     |
FastAPI: backend/security/jwt_verifier.py -- local JWKS verification
     |
backend/security/auth.py: get_current_user() -- extracts verified `sub`
     |
current_user.user_id
     |
backend/api/routes/procurement.py -- passed explicitly into repository calls
     |
backend/persistence/{sqlite,supabase}_repository.py -- WHERE user_id = ... in the query itself
     |
procurement_runs.user_id
```

Independently:

```
Supabase Auth session (if a client connected directly, e.g. via PostgREST)
     |
auth.uid()  (reads the `sub` claim from request.jwt.claims)
     |
RLS policies on procurement_runs
     |
Database-level row visibility/insert restriction
```

Both chains were traced through actual source code (not assumed) and the second was additionally exercised directly against the live database (Section 6).

## 4. RLS Policies (as actually found, live)

Queried directly from `pg_policies` against the real database in this phase:

| Policy | Command | USING | WITH CHECK |
|---|---|---|---|
| `procurement_runs_select_own` | SELECT | `(auth.uid() = user_id)` | — |
| `procurement_runs_insert_own` | INSERT | — | `(auth.uid() = user_id)` |

Exactly these two policies exist — no more, no fewer. No `USING (true)` or other unrestricted policy was found. This matches `supabase/migrations/20260914120000_create_procurement_runs.sql` exactly (no drift between the applied database and the version-controlled file). **No UPDATE or DELETE policy exists** — confirmed both by absence from `pg_policies` and by direct behavioral test (Section 6.3): with RLS enabled and no policy for either command, both are denied by default for any role subject to RLS. This is correct for the current application: no code path anywhere performs an UPDATE or DELETE on `procurement_runs` (Phase 6G/ADR-6's deliberate immutable-snapshot design), so no such policy is needed.

`relforcerowsecurity = False` on the table — expected and not a gap, since `FORCE ROW LEVEL SECURITY` only matters for the table *owner's own* queries, and the owner (`postgres`) is the same role this project's backend uses by design (Section 5).

## 5. Database Role / RLS Interaction

Queried directly: the backend's `DATABASE_URL` connects as role **`postgres`**, which is both the owner of `procurement_runs` and has `rolbypassrls = true`. **This connection bypasses RLS entirely for every query the backend issues.**

This is not a defect — it is the architecture Phase 8A's ADR-5 specified: application-level `WHERE user_id = ...` filtering (verified independently correct, Section 3 of `reports/phase8f_user_owned_persistence.md` and re-confirmed by source inspection this phase) is the **primary** enforcement boundary for the backend's own API. RLS is a **second, independent layer** that would matter if some other client ever connected using the non-privileged `anon`/`authenticated` Postgres roles directly (e.g., a future direct-from-browser Supabase client for a different feature) — and Section 6 proves those roles are, in fact, correctly restricted by RLS, independent of whether the backend's own connection happens to bypass it.

**Both are true simultaneously, and neither substitutes for the other:** the backend's API-level isolation does not depend on RLS at all (confirmed working even though RLS is bypassed for this connection), and RLS itself is confirmed to correctly restrict the roles it actually applies to.

## 6. Real Supabase RLS Verification (direct, live, self-cleaning)

Performed by connecting to the real database with the existing `DATABASE_URL`, then using `SET ROLE` to the standard Supabase `anon`/`authenticated` roles (confirmed via `pg_roles` to have `rolbypassrls = false` — genuinely subject to RLS) and setting the `request.jwt.claims` session variable that Supabase's `auth.uid()` function reads its `sub` from — the same mechanism PostgREST uses internally. This exercises the **actual, real RLS policies**, not a mock or a reading of the SQL text.

**One real, pre-existing `auth.users` account** (from earlier phases' browser testing) was reused as "User A." A second identity ("User B") was represented by a freshly generated UUID not tied to any real account — valid for every SELECT-based test below, since `auth.uid()`'s equality check does not require the compared value to reference an existing user row; only genuinely creating a second REAL signed-up account (blocked by this project's real email-confirmation requirement, confirmed in Phase 8C) would be needed for a full end-to-end *browser* test (Section 6.4).

An initial version of this verification script used a transaction-local `set_config(..., true)` call, which is silently discarded between statements in autocommit mode — this was caught by Test C returning 0 rows for a user reading their own row (an impossible result if the real policy were broken), fixed to use a session-level `set_config(..., false)`, and every test was re-run before any result below was trusted. This is recorded per Rule 1/14: a test harness bug was found and fixed before its results were relied on, exactly as this phase's rules require.

Every row created during this verification was deleted immediately afterward via the privileged connection; **zero permanent rows remain** (confirmed by a final count query).

### 6.1 Results

| Test | Expected | Actual |
|---|---|---|
| A — Anonymous SELECT | Denied | 0 rows visible |
| B — Anonymous INSERT | Denied | `InsufficientPrivilege: new row violates row-level security policy` |
| C — User A reads own row | Allowed | 1 row visible (the correct row) |
| D — User B reads User A's row | Denied | 0 rows visible |
| E — User A inserts own row | Allowed | Insert succeeded |
| F — User A inserts claiming User B's `user_id` | Denied | `InsufficientPrivilege: new row violates row-level security policy` |
| G — User A's unrestricted `SELECT *` never shows another owner's rows | No foreign owners | Confirmed (empty set) |

### 6.2 UPDATE/DELETE default-deny (Section 4)

| Test | Expected | Actual |
|---|---|---|
| UPDATE own row (no UPDATE policy) | 0 rows affected | 0 rows affected; row state unchanged (verified via the privileged connection afterward) |
| DELETE own row (no DELETE policy) | 0 rows affected | 0 rows affected |

### 6.3 What this proves, precisely

RLS genuinely enforces: anonymous denial (SELECT and INSERT), per-user SELECT isolation, per-user INSERT ownership (`auth.uid() = user_id`, not a client-suppliable value), and default-deny for commands with no policy. This is real database behavior, not an inference from reading policy SQL.

### 6.4 What remains NOT VERIFIED at this layer

A full **two-real-account, browser-driven** end-to-end test (two independent Supabase sign-ups, both completing real email confirmation, both signing in through the actual frontend) was **not performed** in this phase — only one real confirmed account exists, and this project's Supabase configuration requires email confirmation (`mailer_autoconfirm: false`, confirmed in Phase 8C), which cannot be completed without a human checking a second real inbox. Creating a second account directly via a hand-crafted `auth.users` INSERT (bypassing Supabase's own Auth service) was deliberately **not** attempted — it risks corrupting Supabase Auth's internal invariants and is exactly the kind of destructive workaround this phase's rules forbid ("do NOT fake the test"). **NOT VERIFIED: real two-account browser-driven RLS exercise.** Section 6.1's Test D substitutes a synthetic second identity, which is sufficient to prove the RLS policy's logic but is not equivalent to a full browser-driven proof with two real, independently authenticated humans.

## 7. Automated Tests Added

**None were added.** The audit found every scenario Step 9 requires already covered by the existing suite:

- `tests/security/test_jwt_verifier.py` (13 tests) — malformed/expired/wrong-signature/wrong-issuer/wrong-audience/missing-`sub`/`alg:none`/unknown-`kid`/key-rotation/JWKS-caching/missing-configuration.
- `tests/security/test_auth.py` (10 tests) — missing header, wrong scheme, unverifiable token, no-internal-leak, valid-token acceptance, invalid-UUID `sub`, request-JSON-spoofing resistance, public `/health`, and the Phase 8E hardening regression test.
- `tests/security/test_ownership.py` (11 tests, T1–T11) — save/list/get ownership for two independently-signed JWT identities, cross-user 404s, unknown run 404, legacy NULL-owner invisibility, request-JSON spoofing.
- `tests/persistence/test_repository.py` / `test_supabase_repository.py` — SQLite and (mocked) Supabase repository ownership filtering, including SQL-injection resistance on both `run_id` and `user_id`.

This is exactly the "LOCAL DETERMINISTIC TESTS" layer (Rule 2) — none of it depends on a real Supabase account or network access, and none of it was weakened or duplicated. **Already correct — no change made.**

## 8. Real Supabase Verification vs. Local/Mocked Tests

| Layer | Method | Result |
|---|---|---|
| JWT verification logic | Local, mocked JWKS (`tests/security/`) | 178 tests passing, unaffected by this phase |
| API-level ownership | Local, mocked repository/JWKS (`tests/security/test_ownership.py`) | Passing |
| **RLS policies themselves** | **Real Supabase Postgres, `SET ROLE` + `request.jwt.claims`** | **Section 6 — real, direct evidence** |
| Real database connectivity | Real Supabase Postgres via the existing `SupabaseProcurementRunRepository.list_runs()` code path | Confirmed working (Session Pooler) |
| Two-real-account browser flow | — | **NOT VERIFIED** (Section 6.4) |

## 9. Secret Hygiene

- `grep -rni "service_role|SUPABASE_SERVICE_ROLE|DATABASE_URL|postgresql://|JWT_SECRET" frontend/src frontend/.env.example` → **no matches.**
- Same check re-run against the actual **built** `frontend/dist` output → **no matches.**
- `grep -rn "print(|logger\.|logging\." backend/` (excluding tests) → **no matches** — no backend code logs anything at all, so no path exists for a token/secret to be logged.
- `.gitignore` confirmed to cover `.env` / `.env.*` with `!.env.example` exception (root-level, applies repo-wide).
- Environment variables were confirmed present/absent as booleans only (`DATABASE_URL configured: yes`, `SUPABASE_URL configured: yes`) — no value was printed, logged, or written into this report at any point.
- The one real `auth.users` UUID used for live verification (Section 6) is an opaque identifier, not a secret, and is not personally identifying on its own; no email address or other PII was printed.

**Already correct — no change made.**

## 10. Regression Verification

- `python -m pytest -q` (run from the project root, both before and after this phase's work): **178 passed, 0 failed, 0 skipped**, both times — identical.
- `npm run build`: succeeds (same pre-existing bundle-size notice as prior phases, unrelated to security).
- `npm run lint`: clean, 0 warnings.

No test was deleted, weakened, or had an assertion changed. No business logic (`backend/core/`, `backend/services/`) was touched — confirmed via `git status`/`git diff` showing zero changes there, consistent with every prior phase since 8D.

## 11. Security Findings

- **Issues found:** None that constitute an actual security defect in the shipped application. RLS policies, application-level ownership filtering, JWT verification, CORS configuration, and frontend secret hygiene were all found already correct.
- **Issues fixed:** None in the application. (One bug was found and fixed in this phase's own *verification script* — Section 6 — a transaction-local `set_config` call that silently no-opped between statements. This is testing-harness hygiene, not an application change, and is recorded to satisfy Rule 1/14's "never assume a test passed" requirement.)
- **Issues intentionally deferred:** `procurement_runs.user_id` remains nullable at the schema level. This is **not** a security gap — both RLS (`auth.uid() = user_id`, never true against `NULL`) and the application-level `WHERE user_id = ...` filter already correctly exclude any NULL-owner row from every authenticated user's view (verified in the original Phase 8F report and unaffected by this phase). The real production table currently contains **zero rows total** (confirmed live), so there is no existing NULL-owner data to migrate. Tightening the column to `NOT NULL` was considered and deliberately **not** done in this phase: it would be a schema change made because it is *possible*, not because a security defect requires it (explicitly against this phase's own Step 3/Step 14 instructions) — every current write path already always supplies a real, verified `user_id`, so the constraint would be enforcing an invariant that already holds in practice.

## 12. Remaining Limitations

- **RLS vs. privileged backend role:** the backend's own connection bypasses RLS entirely (Section 5) — by design, not a gap; application-level filtering is the real boundary for the API, and this was independently re-confirmed correct in this phase.
- **Legacy NULL `user_id` rows:** none currently exist in the real database (confirmed live); the column remains nullable, which is safe given RLS/app-level filtering both already handle a hypothetical NULL row correctly.
- **Manual/Supabase-side verification still open:** a full two-real-account, browser-driven RLS exercise (Section 6.4) requires a second real Supabase account to complete email confirmation — this cannot be done without a human checking a second real inbox, and was not faked.
- **Deferred to a later phase (not this one):** any RLS/schema change beyond what's documented here, frontend auto-sign-out on a stale 401 (already noted in the Phase 8E report), and any production deployment work — none of this was started, per this phase's explicit scope.

## 13. Final Verdict

**PASS WITH DOCUMENTED LIMITATIONS**

Every security invariant this phase set out to verify was verified with real, direct evidence — either against the live Supabase database (RLS enforcement, role/bypass behavior, default-deny for unpoliced commands) or via the existing, comprehensive, passing automated test suite (JWT verification, API-level ownership, cross-user isolation, request-JSON-spoofing resistance). No security defect was found. The one open item (a full two-real-account browser exercise) is explicitly and honestly marked **NOT VERIFIED** rather than assumed, per this phase's own Rule 13 — it does not indicate a known or suspected defect, only an untested path due to a real-world constraint (email confirmation) that this phase correctly declined to work around unsafely.
