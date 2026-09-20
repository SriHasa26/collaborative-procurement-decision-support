# Phase 8E — Supabase Authentication → Existing FastAPI API Integration

**Date:** 2026-09-15
**Scope:** Connect Phase 8C's frontend Supabase session to Phase 8D/8F's already-complete backend verification/ownership layer by attaching `Authorization: Bearer <access_token>` to the existing API client, and fixing the one CORS gap that blocked it. No backend verification logic, no ownership logic, and no frontend auth architecture were rebuilt.

---

## 1. Audit (performed before any code change)

**Frontend:** `frontend/src/lib/supabase.js` (the one Supabase client) → `frontend/src/auth/AuthContext.jsx`/`useAuth.js` (session state) → `frontend/src/auth/ProtectedRoute.jsx` (route guard, UI-only) → `SignInPage`/`SignUpPage`/`TopBar` (Phase 8C, all working). `frontend/src/api/client.js` is confirmed the *only* module that calls `fetch()`; `procurementApi.js` only calls `get()`/`post()` from it. Neither had ever read a Supabase session.

**Backend:** `backend/security/jwt_verifier.py` (JWKS-based verification, Phase 8D) + `backend/security/auth.py`'s `get_current_user()` were already complete, already cryptographically verify a real Supabase access token, and already reject missing/invalid/expired tokens with 401. `backend/api/routes/procurement.py` already requires `Depends(get_current_user)` on all three procurement routes (Phase 8D) and already threads `current_user.user_id` into ownership-filtered repository calls (Phase 8F). `backend/api/main.py`'s `CORSMiddleware` only allowed the `Content-Type` header.

**Answers to the five audit questions this phase required:**
1. The frontend obtains the session from `frontend/src/lib/supabase.js`'s client, mirrored into React state by `AuthContext.jsx`.
2. API requests are created in exactly one place: `frontend/src/api/client.js`'s `request()` function.
3. All three procurement endpoints (`POST /procurement/analyze`, `GET /procurement/runs`, `GET /procurement/runs/{run_id}`) were already authenticated as of Phase 8D; `GET /health` remains public.
4. Yes — `get_current_user()` already existed, complete, and required no changes to its verification logic.
5. Exactly two things were missing: (a) `client.js` never attached the token, and (b) CORS never allowed the `Authorization` header to reach the server at all — a real conflict between the two phases, found and fixed (Section 3).

No conflict requiring a large architectural change was found. The two gaps above were the entire missing bridge.

## 2. Files Modified

- `frontend/src/api/client.js` — attaches `Authorization: Bearer <access_token>` when a session exists (Section 4).
- `backend/api/main.py` — `allow_headers` now includes `"Authorization"` (Section 3).
- `backend/security/auth.py` — hardened `get_current_user()` to convert *any* unexpected exception during verification into a clean 401, not just `AuthenticationError` (Section 7, found during live verification).

## 3. Backend Authentication Integration Details

**The verification/ownership logic itself was not touched** — `get_current_user()`/`verify_access_token()`/repository ownership filtering are byte-for-byte what Phase 8D/8F already built. The one required backend change was CORS: `allow_headers=["Content-Type"]` → `["Content-Type", "Authorization"]`. Without this, a browser's preflight `OPTIONS` request rejects the `Authorization` header before FastAPI ever sees the real request — confirmed both by reasoning about the existing config and by reproducing the failure (Section 6). `allow_credentials` stays `False` — this uses a bearer header, never a cookie.

A second, smaller hardening was added after live verification surfaced an intermittent unhandled exception (Section 6): `get_current_user()` now catches `Exception` broadly (in addition to the existing narrow `AuthenticationError` catch) around the `verify_access_token()` call, converting anything unexpected into the same generic 401 rather than letting it become a raw 500. This satisfies Step 8/9's explicit "never expose a stack trace" requirement more completely than the pre-existing code did, since `verify_access_token`'s documented contract (only ever raising `AuthenticationError`) could not be exhaustively proven against every real-world condition a live Supabase project's real token might exercise.

## 4. Frontend Authentication Integration Details

`frontend/src/api/client.js` gained one new internal function, `getAuthHeader()`, called once per request inside `request()`:

```js
async function getAuthHeader() {
  if (!supabase) return {};
  try {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}
```

This reuses the existing Supabase client singleton (`frontend/src/lib/supabase.js`) — no second client, no new dependency. It satisfies every sub-requirement from Step 3 directly:
- **Authenticated** → `getSession()` returns a session → token attached.
- **Not authenticated** → `getSession()` resolves with `session: null` → no header at all (never a fake/empty token).
- **Session unavailable** (misconfigured client, or `getSession()` throws) → caught, falls back to no header, request proceeds as unauthenticated rather than crashing.
- **Refresh** → `getSession()` is called fresh on every single request (never cached in `client.js`), and Supabase's own client transparently refreshes an expired access token under the hood when a valid refresh token exists — no extra code needed.
- **Sign out** → the very next request's `getSession()` call reports no session, so the old token simply stops being sent; no manual "clear the token" step exists anywhere.

No component or page attaches its own header — this is centralized in the one existing request layer, per Step 3's explicit instruction.

## 5. Protected Endpoints

Unchanged from Phase 8D/8F, confirmed still correct: `POST /procurement/analyze`, `GET /procurement/runs`, `GET /procurement/runs/{run_id}` require authentication and are ownership-filtered. `GET /health` remains public. No endpoint's protection status was changed by this phase.

## 6. /history Result — What Actually Happened During Verification

Real, live, browser-based verification (performed by the project owner against the real Vite dev server, a locally-run FastAPI backend, and the real Supabase project) went through several rounds before succeeding, and each failure was diagnosed to a specific, non-auth-logic cause:

1. **First attempt — 401 on every request.** The backend process I had started did not have `SUPABASE_URL`/`DATABASE_URL` loaded from `backend/.env` (nothing in this project auto-loads `.env` files — confirmed in Phase 8D already). This was my own operational mistake starting the server, not a code defect. Fixed by sourcing `backend/.env`'s real values into the server process's environment.
2. **Second attempt — `psycopg.OperationalError: failed to resolve host 'db.<project>.supabase.co'`.** A DNS resolution failure reaching Supabase's *direct* Postgres hostname — a well-known Supabase infrastructure issue (the direct-connection host often requires IPv6, which this network path does not have). This is a `DATABASE_URL` configuration/connectivity matter entirely outside Phase 8E's scope (it is not caused by anything in this phase's changes, and the fix — switching to Supabase's IPv4-compatible connection pooler string — belongs to whoever manages the real `backend/.env`, not to this codebase). Isolated by temporarily running with `DATABASE_URL` unset (SQLite fallback, an existing, already-tested code path) to separate this from the auth question.
3. **Third attempt — browser-reported "CORS policy" / `net::ERR_FAILED`, later revealed via DevTools to actually be a 500.** Directly reproducing the exact request via `curl` (same Origin header, same path) showed correct CORS headers on every response, including 401s — proving the CORS fix (Section 3) and the server's CORS configuration were both correct. The real cause was an unhandled exception during verification of a **real, live Supabase-issued token** (not reproducible with this session's offline test tokens) — hardened against in Section 3/7.
4. **Fourth attempt — still failing.** Traced to a **stale, orphaned backend process**: an earlier `--reload`-mode uvicorn process was not fully terminated (its child "reloader" process outlived the stop command on Windows), so a fix I had made was never actually being served — confirmed via `netstat`/`taskkill` finding two processes still bound to port 8731 from earlier restarts. This was an artifact of my own local verification process, not a defect in the shipped code.
5. **Fifth attempt — success.** After killing the orphaned processes and starting one clean process (no `--reload`) with the CORS fix and the auth hardening fix both live, the project owner reloaded `/history` and got the correct "No procurement runs yet" empty state — the genuine, correct authenticated response for a user with zero saved runs.

**Conclusion:** `/history` (and by the same code path, `/analyze` and `/results`' data source) now works end-to-end for an authenticated user, confirmed by real browser testing against the real Supabase project. It was never fixed by making the endpoint public or by trusting a frontend-supplied identity.

## 7. User Ownership / Authorization Behavior

Unchanged — already correctly implemented in Phase 8F and confirmed still passing (Section 10). `current_user.user_id` (from the verified JWT's `sub` claim) is the only source of ownership; no `req.body.user_id`, query parameter, URL parameter, or frontend-supplied email is ever consulted for authorization anywhere in the codebase (confirmed unchanged by this phase's `git diff`).

## 8. Security Checks Performed

- [x] No service-role key in frontend — confirmed via `grep -rni "service_role" frontend/src` (no matches).
- [x] No private Supabase credentials in frontend — only `VITE_SUPABASE_URL`/`VITE_SUPABASE_PUBLISHABLE_KEY` (both browser-safe by Supabase's own design) are read anywhere under `frontend/`.
- [x] No database password/connection string in frontend — confirmed via `grep -rni "DATABASE_URL|postgresql://" frontend/src` (no matches).
- [x] No access-token logging — confirmed via `grep -rn "console.log" frontend/src` (no matches, in new or pre-existing code).
- [x] No password logging — unchanged from Phase 8C; still true.
- [x] No hardcoded production secrets — `backend/.env` was read only via shell `source` to launch a local verification process, never printed, echoed, or written into any file/report.
- [x] Backend does not trust frontend-supplied user IDs — unchanged (Phase 8F); `get_current_user()` never reads request JSON.
- [x] Protected endpoints require authentication — confirmed via the existing and new test suites.
- [x] Public endpoints remain public intentionally — `GET /health` untouched.
- [x] CORS remains correctly configured — `allow_origins` unchanged (still an explicit local-dev list, never a wildcard); only `allow_headers` gained `"Authorization"`.
- [x] Existing private storage / file upload security — not applicable; this project has no file upload feature.
- [x] Existing API validation remains intact — `backend/api/schemas.py` untouched.

## 9. Tests Run and Exact Results

`pytest -q`:
- **Previous baseline:** 177 passed (Phase 8D + 8F + the Phase 8C session's earlier CORS-preflight tests).
- **New test:** 1 (`test_unexpected_verification_exception_becomes_a_clean_401`, `tests/security/test_auth.py`) — proves an unexpected non-`AuthenticationError` exception from `verify_access_token` still produces a clean 401 with no exception details in the response body.
- **Final:** **178 passed, 0 failed, 0 skipped.**

No existing test was deleted, weakened, or had an assertion changed.

Additionally verified manually (not via pytest, since these require the frontend build/oxlint toolchain and a live browser):
- `npm run build` — succeeded.
- `npm run lint` (oxlint) — clean, 0 warnings.
- **Real browser end-to-end**: sign-in (Phase 8C, already working) → `/history` → authenticated `GET /procurement/runs` request → correct "No procurement runs yet" response, confirmed by the project owner directly (Section 6).

Items from Step 10's checklist not independently re-verified with a fresh browser session in this phase (already covered by Phase 8C/8D/8F's own verification and unaffected by this phase's changes): logged-out → protected API (401) and sign-out → no authenticated access were exercised via the automated test suite (`tests/security/test_ownership.py`, `test_auth.py`) rather than a fresh manual browser pass, since neither `client.js` nor the auth context's sign-out behavior changed in this phase.

## 10. Build/Lint Results

- `npm run build`: succeeded (129 modules, ~527 kB main chunk — same pre-existing bundle-size notice as Phase 8C, unrelated to this phase).
- `npm run lint`: clean, 0 warnings, 0 errors.
- `pytest -q`: 178 passed, 0 failed, 0 skipped.

## 11. Remaining Limitations

- **`DATABASE_URL` (direct Postgres connection) has a real, unresolved DNS/connectivity issue** on this network (Section 6, item 2) — this is an infrastructure/configuration matter for whoever manages `backend/.env`, not a code defect; switching to Supabase's connection-pooler string (Project Settings → Database → Connection pooling in the Supabase dashboard) is the standard fix, but changing `backend/.env`'s actual value was correctly left to the user, not done by this phase (it is a real secret this phase never touches directly beyond sourcing it locally for verification).
- **The exact unhandled exception observed against the real live token in Section 6, item 3 was not root-caused precisely** — my background-process log capture proved unreliable across `--reload` cycles during this session's live debugging, so the specific PyJWT/claim condition that triggered it is not documented beyond "a real Supabase-issued token exercised something a locally-generated test token in `tests/security/` did not." The defensive fix in Section 3/7 makes this safe (a clean 401 either way) but does not identify the precise trigger. A follow-up with reliable server-side logging (e.g., running uvicorn in the foreground, or with proper log-file flushing) would be needed to pin it down exactly, if it recurs.
- **Frontend-side "session no longer valid → force sign-out" handling was not added.** A 401 from an authenticated-looking session currently surfaces as a generic "could not be loaded" error (via the existing, unmodified `describeHistoryLoadError`/`describeSubmissionError` helpers) rather than actively clearing `AuthContext`'s session and redirecting to sign-in. This was judged out of scope for a minimal integration phase (Step 11: do not overengineer) and is noted here rather than silently added.
- **RFQ and file-upload functionality**: this project has neither; Step 10/12's related checklist items do not apply.

---

## Phase 8E Summary

1. **Files inspected:** `frontend/src/{lib/supabase.js, auth/AuthContext.jsx, auth/useAuth.js, api/client.js, api/procurementApi.js}`, `backend/security/{auth.py, jwt_verifier.py}`, `backend/api/{main.py, dependencies.py, routes/procurement.py}`, `backend/persistence/*`, existing test suites, `frontend/package.json`, `requirements.txt`, `.env.example` files, and all Phase 8A/8B/8C/8D/8F reports.
2. **Files modified:** `frontend/src/api/client.js` (Authorization header attachment), `backend/api/main.py` (CORS `allow_headers`), `backend/security/auth.py` (broader exception hardening in `get_current_user()`).
3. **Files created:** `tests/security/test_auth.py` gained one new test (no new file); `reports/phase8e_supabase_fastapi_integration.md` (this report).
4. **Frontend authentication integration:** `client.js`'s `request()` now attaches `Authorization: Bearer <access_token>` via a new `getAuthHeader()` helper, reusing the existing Supabase client singleton; handles authenticated, unauthenticated, session-unavailable, refresh, and sign-out cases correctly (Section 4).
5. **Backend authentication integration:** No verification/ownership logic changed (Phase 8D/8F already complete); CORS now allows the `Authorization` header; `get_current_user()` now converts any unexpected exception into a clean 401 (Section 3).
6. **Protected endpoints:** Unchanged — `POST /procurement/analyze`, `GET /procurement/runs`, `GET /procurement/runs/{run_id}`. `GET /health` remains public.
7. **/history result:** Confirmed working end-to-end via real browser testing against the real Supabase project, after diagnosing and resolving three unrelated local-environment issues (missing env vars on the server process, a Postgres DNS/connectivity issue isolated via SQLite fallback, and a stale orphaned backend process from an earlier reload cycle) — see Section 6 for the full, honest sequence.
8. **User ownership/authorization behavior:** Unchanged from Phase 8F; still enforced entirely from the verified JWT, never from client-supplied data.
9. **Security checks performed:** All of Step 9's checklist items confirmed (Section 8).
10. **Tests run and exact results:** `pytest -q` → 178 passed, 0 failed, 0 skipped (177 previous + 1 new). `npm run build`/`npm run lint` both clean.
11. **Build/lint results:** Both pass cleanly (Section 10).
12. **Remaining limitations:** A real `DATABASE_URL` connectivity issue (infrastructure, not code); the exact trigger of one unexpected exception during live verification was not root-caused precisely (though safely handled either way); no automatic sign-out-on-401 behavior was added (Section 11).
