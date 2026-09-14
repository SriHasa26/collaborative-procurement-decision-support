# Phase 6F — FastAPI API Layer

**Date:** 2026-09-14
**Scope:** Expose the completed Phase 6B → 6C → 6D → 6E procurement pipeline through a minimal FastAPI HTTP boundary: `GET /health` and `POST /procurement/analyze`. No business logic in route handlers; no database, persistence, authentication, frontend, or ML.

---

## 1. Purpose

Phase 6E produced one clean Python entry point (`ProcurementRunService.run`) but no way to reach it over HTTP. Phase 6F adds exactly that: a thin application boundary that parses an HTTP request into the existing `ProcurementRunInput` contract, calls `ProcurementRunService.run` once, and serializes the resulting `ProcurementRunResult` back to JSON. Nothing about *how* a procurement analysis is computed changes.

## 2. Existing Modules Reused

Inspected directly before writing any code (`backend/models/run_contracts.py`, `backend/services/procurement_run.py`, `backend/models/batch_contracts.py`, `backend/models/contracts.py`, `backend/models/enums.py`, `reports/phase6e_end_to_end_orchestration.md`):

| Component | Reused as-is |
|---|---|
| `ProcurementRunService.run` | ✅ Called exactly once per request, unmodified |
| `ProcurementRunInput` / `ProcurementRunResult` | ✅ The API converts to/from these; no parallel run contract was invented |
| `CommodityParams`, `ProcurementContext`, `TaggedLocation`, `TaggedPrice`, `ConfigParams`, `TransportTier`, `VendorSubmission` | ✅ Every request field maps directly onto these existing dataclasses |
| `VendorLocationStatus`, `PriceGeographicLevel` | ✅ Used directly as Pydantic field types — no duplicate enum |

Confirmed by inspection: no file under `backend/api/` imports `validation.py`, `eligibility.py`, `group_formation.py`, `decision_evaluation.py`, or `selection.py` — only `procurement_run.py`'s public method.

## 3. API Architecture

```
backend/api/
    __init__.py
    main.py            -- FastAPI app, /health, includes the procurement router
    routes/
        __init__.py
        procurement.py  -- POST /procurement/analyze (thin handler only)
    schemas.py          -- Pydantic request models + build_run_input() converter
    serialization.py    -- to_json_safe() generic response converter
```

Minimal, matching the project's existing layering (`backend/models` / `backend/services` split): `schemas.py` is the request-side boundary, `serialization.py` the response-side boundary, `routes/procurement.py` only sequences the two around one `ProcurementRunService.run` call.

## 4. Application Entry Point

`backend/api/main.py`:
```python
app = FastAPI(
    title="Collaborative Procurement Decision-Support API",
    description="...rule-based... NOT AI-powered... no ML-based forecasting...",
    version="0.1.0",
)
```
The description states plainly that the system is rule-based and does not use AI/ML forecasting, restating (not contradicting) Phase 5C's closed research conclusion. No prior versioning convention existed in the project; `0.1.0` was chosen as a conventional pre-1.0 starting point for a newly-exposed API, not tied to any phase number.

## 5. Endpoints

| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/health` | Liveness check — no database exists, so nothing else is checked | 200 |
| POST | `/procurement/analyze` | Runs one full procurement analysis via `ProcurementRunService.run` | 200 (see Section 10) |
| GET | `/docs`, `/openapi.json`, `/redoc` | FastAPI's built-in OpenAPI documentation (automatic, not hand-written) | 200 |

## 6. Request Contract

`ProcurementAnalysisRequest` (`backend/api/schemas.py`) mirrors `ProcurementRunInput` field-for-field: `commodity`, `context`, `vendor_submissions`, `config` — each nested Pydantic model (`CommodityParamsRequest`, `ProcurementContextRequest`, `VendorSubmissionRequest`, `ConfigParamsRequest`, `TaggedLocationRequest`, `TaggedPriceRequest`, `TransportTierRequest`) carries exactly the fields the corresponding existing dataclass already requires — no invented field, no user account/password/phone/payment field (none exist in `VendorSubmission` to begin with). `build_run_input()` converts the validated request into a real `ProcurementRunInput` with no business logic. One request is structurally exactly one `(commodity, context, vendor universe)` — `vendor_submissions` carries no independent commodity tag, so commodity isolation cannot be bypassed at the API layer.

**Deliberately absent:** no numeric-range constraint (`ge=0`, lat/lon bounds) on any request field — those are Phase 6B domain rules (`validate_vendor_structure`) and must keep routing to a per-vendor `VALIDATION_ERROR`, not an HTTP 422 for the whole request (Section 9).

## 7. Response Contract

The route returns `to_json_safe(result)` where `result` is the real `ProcurementRunResult` — no hand-written response schema duplicates its ~15 nested shapes. The JSON therefore exposes, unflattened: `run_status`; the `*_count` input-summary fields; `batch_eligibility` (vendor outcomes, with `reason_code`/`reason_detail`/`demand_provenance`); `group_formation` (pools, candidate groups) or `null`; `final_selection` (every evaluated candidate's base `decision`, `final_decision_state`, `resolving_superset_group_ids`, plus `selected_group_ids`, `total_savings_rs`, `total_vendor_coverage`) or `null`. An empty `selected_group_ids` is returned as `[]`, never omitted or replaced with a fabricated group.

## 8. JSON Serialization Strategy

`backend/api/serialization.py`'s `to_json_safe()` is one small, generic, recursive converter — not a second, parallel Pydantic schema for every existing dataclass (which would duplicate shapes Phase 6A–6E already own). It handles exactly the cases Section 9 of the task spec named: `Enum → .value`, `dataclass → dict` (recursing field-by-field via `dataclasses.fields()`), `tuple/list → list`, `set/frozenset → sorted list` (defensive — no field in this project currently stores a raw `set`), primitives/`None` passthrough. Verified directly by `test_t8_json_serialization_has_no_python_object_leakage`, which walks a real response and asserts no key or value contains a Python `repr`-style fragment (`" object at 0x"`, `"Enum"`, `"DecisionState."`, `"<class "`), and that decision-state strings are clean values like `"BUY_TOGETHER"`.

## 9. API Validation vs Domain Validation

Strictly separated, as required:

| Layer | Example | Mechanism | Result |
|---|---|---|---|
| API/schema (Layer 1) | missing `commodity` field, `vendor_submissions` sent as a string | Pydantic, automatic | `422 Unprocessable Entity` |
| Domain (Layer 2) | negative diary quantity, missing demand evidence, out-of-range coordinate | `validation.py`/`eligibility.py` (unmodified, called inside `ProcurementRunService.run`) | `200 OK`, vendor routed to `VALIDATION_ERROR` or `ABSTAIN`; unrelated vendors unaffected |

Confirmed by `test_t3_mixed_vendor_outcomes` (a request with one domain-invalid vendor still returns 200, with that vendor correctly reported as `VALIDATION_ERROR` and the other vendors proceeding) and `test_t7_malformed_request_*` (missing field / wrong type / invalid JSON all return 422, using the exact same fixture *values* that succeed in T3 to prove the distinction is about request *shape*, not vendor *data*).

## 10. HTTP Status Policy

| Case | Status |
|---|---|
| `GET /health` | 200 |
| `POST /procurement/analyze`, structurally valid (any run outcome: abstentions, validation errors, 0 eligible, 0 groups, 0 selected) | 200 |
| Malformed JSON / wrong type / missing required field | 422 (FastAPI's default `RequestValidationError` handling — not overridden) |
| Unexpected internal exception | 500 (Starlette's default `ServerErrorMiddleware` — not overridden, not caught) |

No blanket `try/except` was added around the route handler or `ProcurementRunService.run` — an unexpected exception propagates to FastAPI/Starlette's own default handling.

## 11. Error Handling

FastAPI's default behavior was used as-is for both the 422 and 500 cases, rather than writing a custom exception handler:
- `RequestValidationError` (422): FastAPI's built-in handler returns a JSON body naming the offending field(s) — no internal detail beyond the request shape itself is exposed.
- An unhandled exception (500): Starlette's default `ServerErrorMiddleware` returns a generic `"Internal Server Error"` response with **no** traceback, file path, or Python `repr` in the HTTP response body, while still logging the full traceback to the server's own console/log stream — satisfying "preserve enough information for debugging through normal application logging" without building new logging infrastructure. This default was verified by inspection of Starlette's `ServerErrorMiddleware` behavior (`debug=False`, FastAPI's own default), not assumed.

## 12. Dependencies

| Package | Status before Phase 6F | Action |
|---|---|---|
| `fastapi` (0.135.2 found installed) | Present in the environment, **not** listed in `requirements.txt` | Added `fastapi>=0.100.0` to `requirements.txt`, matching the project's existing unpinned `>=` convention |
| `httpx` (0.28.1 found installed) | Present in the environment, **not** listed | Added `httpx>=0.24.0` — required by Starlette's `TestClient` for `tests/api/`, a genuine test-only dependency |
| `pydantic` (2.12.5, transitive via `fastapi`) | Present in the environment | **Not** added to `requirements.txt` — it is `fastapi`'s own dependency; pinning it separately would be redundant |

No other package was added. SQLAlchemy, a database driver, Redis, Celery, an authentication library, pandas, and any ML library were confirmed absent from every new file.

## 13. API Tests

`tests/api/test_procurement_api.py`, using FastAPI's `TestClient` (real HTTP requests against the app object, no route function called directly) plus `tests/fixtures/api_fixtures.py` (JSON payloads reusing the exact vendor economics already verified in Phase 6E's own fixtures):

| # | Case | Result |
|---|---|---|
| T1 | Health check | ✅ |
| T2 | Full procurement analysis | ✅ |
| T3 | Mixed vendor outcomes | ✅ |
| T4 | Zero eligible vendors | ✅ |
| T5 | One eligible vendor | ✅ |
| T6 | No compatible groups | ✅ (+ one extra: candidates exist, none selected) |
| T7 | Malformed API request | ✅ (missing field / wrong type / invalid JSON — 3 sub-cases) |
| T8 | JSON serialization | ✅ |
| T9 | Deterministic response structure | ✅ |
| — | Full HTTP→pipeline integration (Section 17) | ✅ `test_full_http_to_pipeline_integration` |

## 14. Full Regression Test Results

```
13 new tests passed, 0 failed, 0 skipped
106 total: passed, 0 failed, 0 skipped
```

| Suite | Tests | Result |
|---|---|---|
| Phase 6A–6E (unchanged) | 93 | ✅ all pass |
| Phase 6F — `tests/api/test_procurement_api.py` | 13 | ✅ all pass |
| **Total** | **106** | **106 passed, 0 failed, 0 skipped** |

No failure was hidden; no existing test was modified.

## 15. Files Created

- `backend/api/__init__.py`, `backend/api/main.py`
- `backend/api/routes/__init__.py`, `backend/api/routes/procurement.py`
- `backend/api/schemas.py`
- `backend/api/serialization.py`
- `tests/api/__init__.py`, `tests/api/test_procurement_api.py`
- `tests/fixtures/api_fixtures.py`
- This report

## 16. Files Modified

- `requirements.txt` — added `fastapi>=0.100.0` and `httpx>=0.24.0`, with an explanatory comment (Section 12).

No file under `backend/core/`, `backend/models/` (existing files), `backend/services/` (existing files), or any prior `tests/`/`reports/` file was changed. No blocking interface problem was encountered.

## 17. Scope Verification

No validation, demand estimation, eligibility, geographic compatibility, graph construction, candidate generation, cost/savings/MOQ/freshness, WAIT/EXPAND, or overlap-resolution logic was reimplemented anywhere under `backend/api/` — confirmed by inspection: `routes/procurement.py` imports only `schemas.build_run_input`, `serialization.to_json_safe`, and `services.procurement_run.ProcurementRunService`. No CORS middleware was added (no frontend exists yet). No `/api/v1/` prefix was introduced (no prior versioning convention exists). No database, persistence, authentication, or ML code exists anywhere in this phase's new files. The closed Potato ML experiment and its underlying data were not read or touched.

## 18. Known Limitations

Phase 6F does **not** implement: a database, persistent storage, user accounts, authentication, authorization, a frontend, CORS integration, real-time market-data acquisition, autonomous ordering, or any machine-learning component. The API is entirely stateless — each `POST /procurement/analyze` request is one independent, in-memory procurement analysis; nothing is retained between requests, and there is no run-history endpoint. These are explicitly out of this phase's scope, deferred to a future, separately-authorized phase.

---

**Files read for this phase:** `backend/models/run_contracts.py`, `backend/services/procurement_run.py`, `backend/models/batch_contracts.py`, `backend/models/contracts.py`, `backend/models/enums.py`, `backend/models/decision_contracts.py`, `backend/models/group_formation_contracts.py`, `reports/phase6e_end_to_end_orchestration.md`, `requirements.txt`.
**Files modified:** `requirements.txt` only, plus the new `backend/api/`, `tests/api/`, `tests/fixtures/api_fixtures.py` additions and this report.
