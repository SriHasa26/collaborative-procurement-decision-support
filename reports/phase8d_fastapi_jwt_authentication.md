# Phase 8D — FastAPI JWT Verification and Verified User Identity

**Date:** 2026-09-14
**Scope:** Local (JWKS-based) cryptographic verification of Supabase-issued access tokens inside FastAPI, a reusable `get_current_user()` dependency, and protecting the three procurement routes with it. Frontend authentication, user-owned persistence/filtering, and any database migration are explicitly out of scope and not implemented here.

---

## 1. Phase Objective

Phase 8A designed the target multi-user architecture; Phase 8B built the database foundation. Phase 8D adds the missing piece between them: a way for FastAPI to know, with cryptographic certainty, *which* real Supabase user is making a request — without trusting anything the client claims in JSON, and without calling out to Supabase on every request. This phase produces exactly that (verification + a dependency + route protection) and nothing beyond it: no route handler was rewritten to filter by user, and no persistence method gained a `user_id` parameter.

## 2. Existing Architecture Inspected

Read completely before writing any code: `reports/phase8a_supabase_multiuser_architecture.md`, `reports/phase8a_architecture_decision_record.md` (ADR-3, ADR-4, ADR-5 are directly load-bearing here), `reports/phase8a_migration_roadmap.md`, `reports/phase8b_supabase_database_foundation.md`. Also inspected directly: `backend/api/{dependencies,main,schemas}.py`, `backend/api/routes/procurement.py`, `backend/persistence/repository.py`, `backend/.env.example`, `requirements.txt`, `supabase/migrations/20260914120000_create_procurement_runs.sql`, `tests/api/conftest.py`, `tests/api/test_dependencies.py`.

Confirmed via `pip show`: `PyJWT` 2.10.1 and `python-jose` 3.5.0 were both already installed (transitively, before this phase made either a direct dependency), plus `cryptography` 46.0.5. `authlib` was not present. Confirmed via `grep -n "user_id" backend/api/schemas.py`: no request schema has ever had a `user_id` field.

## 3. Architectural Ambiguity Resolved (Read First)

Supabase projects can, depending on age and configuration, sign access tokens either asymmetrically (RS256/ES256, verifiable via a published JWKS — the mechanism this phase's own instructions describe throughout) or, in older configurations, symmetrically with a shared `SUPABASE_JWT_SECRET` (HS256). These two require genuinely different verification code — a JWKS-based verifier cannot verify an HS256 token, and vice versa.

This phase's instructions describe *only* the JWKS/local-verification architecture, in detail, and never mention a shared secret or HS256 as an alternative anywhere. Given that, and given that making a live call to the user's real Supabase project to determine which mechanism it actually uses is exactly the kind of "touch real credentials during this coding phase" action these instructions forbid, the JWKS/asymmetric architecture was implemented exactly as directed, and this assumption is recorded here rather than silently made. **This has not been independently confirmed against the live project.** If the project turns out to use the legacy HS256 mechanism, every real request will fail closed (rejected as unverifiable, per Section 8's error handling — never silently accepted), not fail open — so this assumption is wrong-safe if incorrect, but it is still an assumption, not a confirmed fact, and should be verified before Phase 8D's authentication is relied upon against the real project.

## 4. Dependency Selection

Added one direct dependency: **`PyJWT[crypto]>=2.8`** (already present transitively; now pinned directly and documented in `requirements.txt`). No other package was added.

`python-jose` (already installed) was considered and rejected: source inspection of PyJWT's own `jwt.PyJWKClient` (`get_signing_key`, `get_jwk_set`, `fetch_data`) showed it already implements exactly the bounded JWKS cache and "unknown kid → refresh once → clean failure" behavior this phase requires, so no hand-rolled caching/refresh logic — and no second JWT library — was needed. The Supabase Python client, Firebase SDK, SQLAlchemy, Redis, and Celery were all correctly out of scope and were not added or considered further.

## 5. Module Structure

```
backend/security/
    __init__.py       -- package docstring only
    jwt_verifier.py    -- pure JWT/JWKS verification (no FastAPI import)
    auth.py            -- FastAPI dependency + AuthenticatedUser model
```

A new top-level package, mirroring this project's existing convention of one package per concern (`backend/core/`, `backend/persistence/`, `backend/services/`). `jwt_verifier.py` has no FastAPI/HTTP concept at all — it raises a plain `AuthenticationError` — so it is independently unit-testable and keeps the "auth logic must never leak into the decision engine" boundary sharp by keeping it out of `backend/api/` too. `auth.py` is the only file that knows about FastAPI, `HTTPException`, or HTTP status codes.

## 6. JWT Verification Design (`backend/security/jwt_verifier.py`)

`verify_access_token(token: str) -> dict`:
1. Reads `SUPABASE_URL` from the environment; raises `AuthenticationError` if unset.
2. Derives the JWKS URL (`<SUPABASE_URL>/auth/v1/.well-known/jwks.json`) and the expected issuer (`<SUPABASE_URL>/auth/v1`).
3. Obtains a cached `jwt.PyJWKClient` for that JWKS URL (see Section 7) and resolves the token's signing key via `get_signing_key_from_jwt` — this is what performs the "unknown kid → refresh once → fail" behavior.
4. Calls `jwt.decode(token, signing_key.key, algorithms=ALLOWED_ALGORITHMS, audience=..., issuer=..., options={"require": ["exp", "sub", "iss", "aud"]})`.
5. Any `jwt.exceptions.PyJWTError` from either step (malformed token, bad signature, expired, wrong issuer/audience, missing required claim, unresolvable key) is caught and re-raised as a plain `AuthenticationError` — the original exception is chained (`from exc`) for local debugging only, never exposed to a caller.

`ALLOWED_ALGORITHMS = ["RS256", "ES256"]` is a fixed list passed explicitly to `jwt.decode`; PyJWT rejects any token whose header names an algorithm outside this list — including `"none"` — before attempting verification. The algorithm is never read from, or chosen based on, the token itself.

## 7. JWKS Handling and Caching

Rather than hand-rolling a cache, this module reuses `jwt.PyJWKClient` directly, confirmed by reading its source to already implement:
- A bounded `JWKSetCache` with a 300-second default lifespan (`cache_jwk_set=True` by default).
- `get_signing_key(kid)`'s existing logic: look up `kid` in the cached set → on a miss, refresh the set **exactly once** → look up again → raise `PyJWKClientError` cleanly if still missing. No infinite loop is possible.

The one piece of glue code this phase adds is `_get_jwk_client(jwks_url)`, wrapped in `functools.lru_cache(maxsize=1)`, so the **same** `PyJWKClient` instance (and therefore the same `JWKSetCache`) is reused across requests within a process — constructing a fresh client per request would reset the cache every time and reintroduce a per-request fetch, which is explicitly forbidden. `reset_jwk_client_cache()` clears this for tests only; production code never calls it.

## 8. Key Rotation Behavior

Key rotation is handled by the exact same mechanism as an unknown `kid` (Section 7) — a token signed with a newly-rotated key has a `kid` the cached JWKS doesn't recognize yet, which triggers the one-time refresh and picks up the new key. No separate rotation-specific code exists; this is deliberate, since a dedicated "rotation handler" would just be duplicating the unknown-`kid` path. Verified directly by `tests/security/test_jwt_verifier.py::test_key_rotation_new_key_validates_after_refresh`.

## 9. Authenticated User Identity (`backend/security/auth.py`)

`AuthenticatedUser` is a frozen dataclass with exactly two fields: `user_id: str` and `email: Optional[str]`. It is not a full user/profile model and does not duplicate `auth.users` — it carries only what a verified token actually proves.

`get_current_user()` is a FastAPI dependency (`Depends(_bearer_scheme)`, where `_bearer_scheme = HTTPBearer(auto_error=True)`) that:
1. Calls `verify_access_token(credentials.credentials)`; any `AuthenticationError` becomes `HTTPException(401, "Invalid authentication token")`.
2. Reads `sub` from the verified claims and requires it parse as a `uuid.UUID`; any failure (missing, non-UUID) also becomes the same 401.
3. Reads `email` from the claims only if it is present and a string; otherwise `email` is `None`. Never falls back to any other source.

`HTTPBearer(auto_error=True)`'s own behavior (confirmed by reading the installed `fastapi` 0.135.2 source directly) already returns HTTP 401 with a generic `"Not authenticated"` detail — not FastAPI's older HTTPBasic-style 403 — for both a missing `Authorization` header and a non-`Bearer` scheme, and never echoes header contents back. This was reused rather than duplicated.

## 10. Protected vs. Public Endpoints

**Protected** (require `Depends(get_current_user)`), per Phase 8A's own design (all persist or return user-relevant data): `POST /procurement/analyze`, `GET /procurement/runs`, `GET /procurement/runs/{run_id}`.

**Public** (unchanged): `GET /health` (no data, existed before authentication, per this phase's own explicit instruction to keep it public). API docs (`/docs`, `/openapi.json`) were not touched and remain public — restricting them was never in scope.

## 11. Request JSON Cannot Control Identity

`ProcurementAnalysisRequest` (`backend/api/schemas.py`) has no `user_id` field and was not modified. Pydantic's default behavior (`extra="ignore"`) means a client-supplied `"user_id"` in the JSON body is silently dropped, never read. More fundamentally, `get_current_user()` never inspects the request body at all — it only reads the `Authorization` header — so there is no code path through which request JSON could influence the authenticated identity even if a `user_id` field existed. Verified directly by `tests/security/test_auth.py::test_request_json_cannot_override_authenticated_identity`, which sends a request with an attacker-chosen `user_id` field alongside a valid token for a *different* real user id and confirms the request succeeds purely on the verified token's own merits (the extra field has no effect one way or the other).

## 12. Scope Boundary Deliberately Not Crossed

Per this phase's own explicit instruction, `current_user` is accepted as a dependency on all three routes (proving the request is authenticated) but is **not** used for anything beyond that: `repository.save_run`/`list_runs`/`get_run` are byte-for-byte unchanged, no `user_id` is written or filtered by, and `backend/persistence/repository.py`'s `ProcurementRunRepository` interface still has no `user_id` parameter anywhere. Each handler contains an explicit `del current_user` with a comment stating this is intentional and deferred to Phase 8F. Any authenticated user can currently list or retrieve any run — identical to this project's pre-8D behavior — this is Phase 8D's honest, documented limitation, not an oversight.

## 13. Environment Variables

`backend/.env.example` updated:
- `SUPABASE_URL` — activated (was reserved/commented since Phase 8B). Used to derive both the JWKS URL and the expected issuer.
- `SUPABASE_JWT_AUDIENCE` — new, optional, commented out; defaults to `"authenticated"` (Supabase's standard audience claim) when unset.
- `SUPABASE_JWT_SECRET` — **removed**, not merely left commented. That name implies the legacy HS256/shared-secret mechanism (Section 3); this phase implements JWKS-based verification exclusively, which never reads a shared secret. Keeping an unused, misleadingly-named placeholder around was judged worse than removing it, with the reasoning recorded here and in the file itself.
- `SUPABASE_SERVICE_ROLE_KEY` — still reserved/commented, unchanged; still not read by any code (Phase 8F's concern).

No real value for any of these was ever set, read from, written to, or committed anywhere in this phase. No `backend/.env` file exists in this project.

## 14. Testing Strategy

All new tests are fully offline: every JWT is signed locally against an RSA keypair generated in-process by `cryptography` (`tests/security/conftest.py`), and the only thing ever faked is the network transport — `urllib.request.urlopen` is monkeypatched to return an in-memory fake HTTP response built from a small `FakeJwksServer` test helper. This specific boundary (not `PyJWKClient.fetch_data` itself) was chosen deliberately: an earlier attempt to monkeypatch `fetch_data` directly silently broke JWKS caching, because the real `fetch_data`'s own `finally: self.jwk_set_cache.put(...)` — the exact line that makes caching work — never ran. Patching one level lower, at `urlopen`, lets every line of `PyJWKClient`'s real fetch/cache/refresh/parse logic execute genuinely, which is what actually exercises the caching and key-rotation requirements truthfully rather than just asserting against a mock.

`tests/security/conftest.py`'s `isolated_repository` fixture (mirroring `tests/api/conftest.py`'s fixture of the same name) redirects `get_repository` to a `tmp_path` SQLite file, so `tests/security/test_auth.py`'s real requests through the app never touch the real database. Unlike `tests/api/conftest.py`, it does **not** override `get_current_user` — that package exists specifically to exercise real authentication end-to-end.

`tests/api/conftest.py` gained a second autouse fixture, `bypass_authentication`, which overrides `get_current_user` (via the same `app.dependency_overrides` mechanism already used for `get_repository`) with a fixed fake `AuthenticatedUser` for every test under `tests/api/`. This was necessary because those pre-existing tests predate authentication and test persistence/business-logic behavior, not authentication itself; without this override, adding `Depends(get_current_user)` to the routes would have broken all of them with 401s. No assertion in any pre-existing test file was touched — only a new, additive fixture was introduced, following the exact override technique the project already established for `get_repository` in Phase 6G/8B.

## 15. Tests Added

`tests/security/test_jwt_verifier.py` (13 tests) — pure verification logic:
valid token verified; malformed token rejected; expired token rejected; invalid signature rejected (signed with a different key than the one published under the claimed `kid`); wrong issuer rejected; wrong audience rejected; missing `sub` rejected; `alg: none` never accepted; unknown `kid` triggers exactly one refresh then succeeds; a truly unknown `kid` fails cleanly without looping (fetch count capped at 2 — priming + one refresh); key rotation validates the new key; JWKS is not re-fetched on repeated calls once cached; missing `SUPABASE_URL` is rejected.

`tests/security/test_auth.py` (10 tests) — the FastAPI dependency and route wiring: all three protected endpoints reject a missing `Authorization` header (parametrized); wrong auth scheme rejected; an unverifiable token is rejected; the 401 response body contains none of `jwks`/`signing key`/`traceback`/`secret`/`rsa`/`-----BEGIN`; a valid authenticated request succeeds; a non-UUID `sub` is rejected; a request-JSON `user_id` field cannot override the token-derived identity; `GET /health` remains public with no auth required.

## 16. Test Results

- **Previous (pre-Phase-8D) baseline:** 134 passed.
- **New tests added:** 23 (13 + 10).
- **Final:** `python -m pytest -q` → **157 passed, 0 failed, 0 skipped.**

Zero real network access, zero real Supabase credentials, zero real user accounts, and zero real JWTs were used anywhere in the run.

## 17. Files Created

- `backend/security/__init__.py`
- `backend/security/jwt_verifier.py`
- `backend/security/auth.py`
- `tests/security/__init__.py`
- `tests/security/conftest.py`
- `tests/security/test_jwt_verifier.py`
- `tests/security/test_auth.py`
- `reports/phase8d_fastapi_jwt_authentication.md` (this file)

## 18. Files Modified

- `backend/api/routes/procurement.py` — added `current_user: AuthenticatedUser = Depends(get_current_user)` to all three routes, each with an explicit `del current_user` and a comment on why it's unused (Section 12).
- `requirements.txt` — added `PyJWT[crypto]>=2.8` with a reasoning comment matching the file's existing convention.
- `backend/.env.example` — activated `SUPABASE_URL`, added `SUPABASE_JWT_AUDIENCE`, removed `SUPABASE_JWT_SECRET` (Section 13).
- `tests/api/conftest.py` — added the `bypass_authentication` autouse fixture (Section 14). No existing fixture or assertion changed.

**Not modified:** `backend/api/dependencies.py`, `backend/persistence/repository.py`, `backend/persistence/sqlite_repository.py`, `backend/persistence/supabase_repository.py`, `backend/api/schemas.py`, `backend/api/main.py`, `backend/core/`, `backend/services/`, `backend/models/`, `supabase/migrations/`, anything under `frontend/`.

## 19. Frontend Modifications

**None.** No file under `frontend/` was read for editing, written, or edited during this phase. `git status --short frontend/` was run and shows only pre-existing uncommitted changes from earlier phases (7A–7G) that predate this session — none of them were created or touched during Phase 8D.

## 20. Database Modifications

**None.** `supabase/migrations/` was not modified, and no new migration file was created. No defect in the existing migration (`20260914120000_create_procurement_runs.sql`) was found that would have required one. No RLS policy was changed. No DDL was executed against any database, real or local.

## 21. Security Audit (18 checks)

1. **No `user_id` from request JSON** — confirmed (Section 11).
2. **Signature cryptographically verified** — `jwt.decode` against the JWKS-resolved public key; confirmed by `test_invalid_signature_is_rejected`.
3. **Expiration validated** — `exp` required and checked by `jwt.decode`; confirmed by `test_expired_token_is_rejected`.
4. **Issuer validated** — `issuer=` param; confirmed by `test_incorrect_issuer_is_rejected`.
5. **Audience validated** — `audience=` param; confirmed by `test_incorrect_audience_is_rejected`.
6. **Algorithm restricted** — fixed `ALLOWED_ALGORITHMS` list, never derived from the token.
7. **`alg: none` rejected** — confirmed by `test_alg_none_is_never_accepted`.
8. **Unknown `kid` doesn't bypass verification** — fails closed after one refresh; confirmed by `test_unknown_kid_that_still_does_not_exist_fails_cleanly_without_looping`.
9. **JWKS not fetched every request** — cached `PyJWKClient` singleton + its own 300s cache; confirmed by `test_jwks_is_not_fetched_on_every_call_once_cached`.
10. **Key rotation handled** — confirmed by `test_key_rotation_new_key_validates_after_refresh`.
11. **Auth errors don't leak secrets** — single generic `"Invalid authentication token"` detail; confirmed by `test_error_response_does_not_leak_internals`.
12. **Protected endpoints reject missing tokens** — confirmed by the parametrized `test_protected_endpoint_rejects_missing_authorization_header`.
13. **Health endpoint public** — confirmed by `test_health_endpoint_remains_public`.
14. **Decision engine has no auth logic** — `backend/core/` untouched; verified via `git status --short backend/core/` (no changes) and by construction (no import of `backend.security` anywhere under `backend/core/` or `backend/services/`).
15. **Frontend not modified** — confirmed (Section 19).
16. **No real credentials committed** — `backend/.env.example` has blank/placeholder values only; test fixtures use a placeholder `https://test-project.supabase.co` that is never actually contacted (only monkeypatched transport is used).
17. **Existing tests pass** — all 134 pre-existing tests still pass, unmodified in assertion content.
18. **Tests run offline** — confirmed (Section 14); zero network calls, zero real Supabase access.

## 22. Problems or Ambiguities Found

The JWKS-vs-HS256 algorithm ambiguity (Section 3) was found and is documented as a recorded assumption rather than silently resolved or ignored — this is the one point in this phase where a real architectural question existed and is flagged rather than guessed past silently.

One implementation pitfall was found and fixed during testing, not in production code: mocking `PyJWKClient.fetch_data` directly (rather than the lower-level `urllib.request.urlopen` it calls) silently defeated the library's own caching, because `fetch_data`'s real `finally` block (which populates the cache) never ran under that mock. This was caught by a failing test (`fetch_count` incrementing on every call instead of staying flat) before it could produce a false sense of test coverage, and fixed by mocking one level lower instead (Section 14).

## 23. Known Limitations

- **This is not "Supabase authentication is fully complete."** There is no frontend login/signup/logout UI, no Supabase JS client, and no React auth context — a browser cannot yet obtain a token to send. Authentication only exists as a backend verification capability today.
- **No persistence is user-scoped yet.** Any authenticated user (any real Supabase user with a valid token) can currently list and retrieve any run — identical to pre-8D behavior, since Phase 8D deliberately does not filter by `user_id` (Section 12). This is Phase 8F's job.
- **The JWKS-vs-HS256 assumption (Section 3) is unconfirmed** against the live Supabase project.
- **RLS policies remain unexercised end-to-end** by any real authenticated request, since FastAPI still connects with its own privileged connection (Phase 8A ADR-5) — Phase 8G's concern, unchanged from Phase 8B's own stated limitation.
- **`SUPABASE_JWT_AUDIENCE`/issuer derivation have not been validated against a real Supabase-issued token** — only against locally-generated test tokens with the same claim shapes Supabase documents using.

## 24. Recommended Next Phase

Per the existing roadmap (`reports/phase8a_migration_roadmap.md`), Phase 8C (frontend auth UI) or Phase 8E/8F (wiring the now-available verified identity into persistence) are the logical next steps; both were explicitly out of scope here and are not started. Before either, confirming Section 3's algorithm assumption against the real project (e.g., by having the user share which signing algorithm their project's JWTs actually use, without sharing any secret) would remove the one open unknown this phase could not resolve safely on its own.

---

## Phase 8D Summary

**Status:** Complete. All required JWT verification, JWKS handling, the `get_current_user()` dependency, and route protection were implemented; all 16 required test scenarios are covered; all 18 security-audit checks pass.

**Authentication architecture implemented:** Local, JWKS-based verification of Supabase access tokens inside FastAPI (`backend/security/jwt_verifier.py` + `backend/security/auth.py`) — no per-request call to Supabase's own auth endpoint.

**JWT verification method:** `jwt.decode()` (PyJWT) with an explicit algorithm allow-list (`RS256`, `ES256`), issuer, audience, and expiration all validated; signing key resolved via JWKS.

**JWKS handling and caching:** `jwt.PyJWKClient`, reused as a process-lifetime singleton (`functools.lru_cache(maxsize=1)`) so its own built-in bounded cache (300s default lifespan) persists across requests — no per-request fetch.

**Key rotation behavior:** Handled automatically via the same "unknown `kid` → one refresh → retry" path `PyJWKClient` already implements; verified with a real rotation scenario in tests.

**Authenticated user identity:** `AuthenticatedUser(user_id: str, email: Optional[str])` — `user_id` from the verified `sub` claim only, validated as a UUID; never from request JSON.

**Protected endpoints:** `POST /procurement/analyze`, `GET /procurement/runs`, `GET /procurement/runs/{run_id}`.

**Public endpoints:** `GET /health`; API docs (unchanged).

**Request JSON security:** No request schema has a `user_id` field; `get_current_user()` never reads the request body; proven by a dedicated test sending a spoofed `user_id` alongside a valid token for a different real user.

**Dependencies added:** `PyJWT[crypto]>=2.8` (was already installed transitively; now a direct, pinned dependency). No other package added.

**Tests added:** 23 (`tests/security/test_jwt_verifier.py`: 13; `tests/security/test_auth.py`: 10).

**Test results:** Previous: 134 passed. New: 23 passed. **Final: 157 passed, 0 failed, 0 skipped.**

**Files created:** `backend/security/{__init__.py, jwt_verifier.py, auth.py}`, `tests/security/{__init__.py, conftest.py, test_jwt_verifier.py, test_auth.py}`, this report.

**Files modified:** `backend/api/routes/procurement.py`, `requirements.txt`, `backend/.env.example`, `tests/api/conftest.py` (additive fixture only).

**Frontend modifications:** None. Verified via `git status --short frontend/` — all listed changes predate this phase.

**Database modifications:** None. `supabase/migrations/` untouched; no new migration; no RLS change.

**Security audit:** All 18 checks pass (Section 21).

**Problems or ambiguities found:** The Supabase JWKS-vs-HS256 signing-algorithm question (Section 3) — proceeded with JWKS per the task's own exclusive description, documented as an unconfirmed assumption rather than resolved silently.

**Known limitations:** No frontend auth exists yet; no persistence is user-scoped yet; RLS remains unexercised by real traffic; the algorithm assumption above is unconfirmed against the live project.

**Recommended next phase:** Confirm the algorithm assumption if possible, then proceed to Phase 8F (wire verified identity into persistence) or Phase 8C (frontend auth UI) per the existing roadmap — both remain unstarted.
