# Phase 8F — Authorization, Data Ownership & Security Audit

**Date:** 2026-09-15
**Scope:** Audit-first pass over authorization, data ownership, Supabase RLS, storage security, and real database connectivity, following Phase 8E's frontend↔backend integration and the `DATABASE_URL` change from Supabase's direct connection to the Session Pooler. This is a verification/audit report, not a rebuild — it documents what was inspected, what was proven correct with live evidence, and confirms **zero code changes were required**.

**Note on naming:** an earlier report, `reports/phase8f_user_owned_persistence.md`, already covers the *implementation* of user-owned persistence (repository ownership filtering, SQLite schema evolution, cross-user isolation tests). This report is the follow-up *audit* of that same work plus everything Phase 8E added, using a real, now-working database connection to verify claims that were previously only assumptions.

---

## 1. Audit Findings

Every area this phase was asked to inspect was found **already correct**, with one exception: a previously-unverified assumption (Phase 8A ADR-5's "the backend connection bypasses RLS") could now be checked with a real, working database connection for the first time — and was confirmed true (Section 6.2). No security defect, no dangerous RLS policy, and no missing ownership check was found anywhere. Consequently, **no backend, frontend, or migration file was changed in this phase.**

## 2. Authorization Status — Already correct, no change made

- `backend/security/auth.py`'s `get_current_user()` derives identity exclusively from the verified JWT's `sub` claim (unchanged since Phase 8D, hardened further in Phase 8E to fail closed on any unexpected error — Section 7 of the Phase 8E report).
- `grep -rni "user_id|userid|owner_id" backend/api/schemas.py backend/models/` returns **zero matches** — no request schema or domain model has ever had a client-suppliable identity field for the backend to accidentally trust.
- `backend/api/routes/procurement.py` passes `current_user.user_id` (never anything from `payload`) into every repository call.

## 3. User Ownership Status — Already correct, no change made

`backend/persistence/{sqlite,supabase}_repository.py` (Phase 8F, prior report) enforce ownership **inside the SQL itself**:
- `save_run(user_id, ...)` writes `user_id` as part of the same `INSERT`.
- `list_runs(user_id, ...)` filters with `WHERE user_id = ...`.
- `get_run(user_id, run_id)` filters with `WHERE run_id = ... AND user_id = ...` in one query — never fetch-then-check.

This was re-verified against the **live** database in this phase (Section 6.1), not just the SQLite-backed test suite.

## 4. RLS Status — Already correct, no change made

Live, read-only audit of the real Supabase project (not just the migration file) confirms:

```
RLS enabled on procurement_runs:      relrowsecurity = True
Force RLS:                            relforcerowsecurity = False   (expected -- see 6.2)

Live policies (pg_policies), exactly two, matching the migration file:
  procurement_runs_select_own  | SELECT | USING (auth.uid() = user_id)
  procurement_runs_insert_own  | INSERT | WITH CHECK (auth.uid() = user_id)
```

No `UPDATE`/`DELETE` policy exists (none is needed — no code path performs either operation, per ADR-6), and RLS being enabled with no such policy means Postgres denies those operations by default for any non-owner role — the secure default. **No dangerous policy (e.g. `USING (true)`) was found.** The live database schema was also confirmed to exactly match `supabase/migrations/20260914120000_create_procurement_runs.sql` (column names, types, and `user_id`'s intentional nullability) — no drift between the applied migration and the file in this repo.

## 5. Storage Security Status — Not applicable

`grep -rni "storage|bucket|signed[_-]?url" backend/ frontend/src/` found no Supabase Storage usage anywhere in this project — the two frontend matches are the Supabase Auth SDK's own internal session-storage references (unrelated to file storage), and the one backend match is an unrelated comment ("no storage engine... decision is made here"). **This project has no file upload/document storage feature.** Section 7's checklist does not apply.

## 6. Database Connectivity Status

### 6.1 Real, live verification (not just `/health`)

Per this phase's explicit instruction not to trust `/health` alone, `SupabaseProcurementRunRepository.list_runs()` — the exact, unmodified, existing repository method the API uses — was called directly against the real database using the newly-configured Session Pooler `DATABASE_URL`:

```
REAL DB QUERY SUCCEEDED via existing repository.list_runs() -- pooler connection works.
Result for a nonexistent user_id (expected empty): []
```

This is a genuine round trip through psycopg, the real network, and the real Postgres instance — not a mock. **The Session Pooler connection string works correctly** through the existing, unmodified application code path. (A live INSERT via `save_run()` was deliberately not performed for this audit, to avoid leaving a permanent, undeletable synthetic row in the real production table — this project's repository interface has no delete method by design, ADR-6 — but `list_runs`/the RLS/schema queries in Section 6.2 already prove the connection, credentials, and query execution all work correctly.)

### 6.2 ADR-5's assumption, now confirmed with live evidence

Phase 8A/8B/8D/8F's reports repeatedly documented an *assumption*, never previously verified with a working connection: that the backend's own database connection is privileged and bypasses RLS. With the pooler connection now working, this was checked directly:

```
connection role:   {'current_user': 'postgres', 'session_user': 'postgres'}
role privileges:   {'rolname': 'postgres', 'rolsuper': False, 'rolbypassrls': True}
table owner:       {'tableowner': 'postgres'}
```

**Confirmed, not assumed:** the backend connects as `postgres`, which both owns `procurement_runs` and has the explicit `BYPASSRLS` attribute. RLS genuinely does not apply to any query this backend issues. This is exactly the architecture ADR-5 called for (application-level `WHERE user_id = ...` filtering as the *primary* enforcement layer, RLS as an independent second layer for any other, non-privileged connection) — it is not a gap, and closing it (e.g., by connecting as a restricted role) was correctly out of scope, since it would be a genuine architectural change this audit's own rules forbid making speculatively. It is reported here as newly-**confirmed fact** rather than left as an open assumption in future reports.

## 7. User A → User B Isolation Test Result

Already fully covered by `tests/security/test_ownership.py` (built in the earlier Phase 8F implementation, unaffected by Phase 8E): two independently-signed JWTs for two distinct users prove, end-to-end through the real HTTP layer:
- User A can save, list, and retrieve their own run.
- User B can save, list, and retrieve their own run.
- User A **cannot** list User B's runs, retrieve User B's run (404), or influence User B's ownership via a spoofed `user_id` in request JSON.
- The reverse (User B → User A) holds symmetrically.
- A legacy NULL-owner row is invisible to both.

Re-run in this phase as part of the full suite (Section 11) — **all still pass, unchanged.** No new test was needed; this scenario was already exactly what Phase 8F's original test suite was built to prove.

## 8. 401/403 Behavior

- **No authentication** → `401 Unauthorized` (`HTTPBearer`, unchanged).
- **Invalid/expired JWT** → `401 Unauthorized` (`get_current_user`, unchanged, now hardened in Phase 8E to also catch unexpected exceptions).
- **Authenticated user requesting another user's resource** → **`404 Not Found`**, not `403`. This is a deliberate, already-documented choice (`reports/phase8a_architecture_decision_record.md` ADR-3): returning `403 "that run belongs to another user"` would confirm the run_id exists at all, an IDOR/information-disclosure risk this project's own architecture explicitly decided to avoid. This is precisely the "intentionally non-disclosing response" this phase's own instructions (Section 5) anticipated as an acceptable alternative to 403 — **already correct, no change made.**
- `GET /health` — unchanged, still public, still `200`.

## 9. Tests

- **Previous baseline:** 178 passed.
- **Current result:** `python -m pytest -q` (run from the project root) → **178 passed, 0 failed, 0 skipped.**
- No new test was added — the audit found the existing `tests/security/test_ownership.py`, `test_auth.py`, `test_jwt_verifier.py`, `test_dependencies.py`, and persistence test suites already fully cover this phase's required scenarios (User A/B isolation, 401 behavior, ownership enforcement, request-JSON-spoofing resistance).

## 10. Frontend Build/Lint Result

No frontend file was changed in this phase. Re-run anyway for a fresh confirmation: `npm run build` succeeded (same pre-existing bundle-size notice as Phase 8C/8E, unrelated); `npm run lint` (oxlint) — clean, 0 warnings.

## 11. Exact Files Changed

**None.** This phase made zero modifications to backend, frontend, or test files — every area audited was found already correct.

## 12. Exact Migrations Created

**None.** The existing migration (`supabase/migrations/20260914120000_create_procurement_runs.sql`) was found, via live database inspection, to exactly match what is actually applied to the real project — no drift, no missing policy, no dangerous policy. Creating a new migration would have been unjustified per this phase's own "only if the audit proves one is required" rule.

## 13. Remaining Blockers

None identified. The one previously-open item from `reports/phase8e_supabase_fastapi_integration.md` (`DATABASE_URL`'s DNS/connectivity issue with the direct-connection host) is resolved — confirmed working via the Session Pooler string (Section 6.1).

## 14. Production Readiness Assessment

**Backend authorization and ownership enforcement: production-ready** for the scope this project defines (single-table procurement runs, no file storage, no admin/role system). Specifically:
- Identity is cryptographically verified from a real Supabase JWT on every protected request; never trusted from client input.
- Ownership is enforced in the database query itself, for both the SQLite (offline/dev) and Supabase (production) repositories, verified with live evidence in this phase.
- Cross-user access returns a non-disclosing 404, closing a real IDOR class the project's own ADR anticipated.
- RLS is correctly configured as a defense-in-depth layer, confirmed to exactly match the version-controlled migration, with no dangerous policy.
- The real production database connection (Session Pooler) now works end-to-end through the unmodified application code.

**Still outside this project's current scope** (unchanged from earlier phases, not defects): the frontend does not yet handle a 401 on an already-authenticated session by forcing sign-out (Phase 8E, Section 11); there is no file storage feature to assess; and full multi-browser, multi-real-account testing against the live Supabase project (as opposed to this phase's locally-signed-JWT test suite plus live read-only database checks) has still not been performed — a reasonable next step would be exactly that, using two real Supabase accounts, if the project wants end-to-end production sign-off beyond what an audit of the existing, already-tested code can provide.
