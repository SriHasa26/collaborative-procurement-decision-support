# Phase 7C — Procurement Analysis Input Form

**Date:** 2026-09-14
**Scope:** Build the real procurement analysis input form on the Analyze page — form state, vendor list management, structural validation, and exact request-payload preparation. No backend submission, no backend/database changes, no Results/History integration.

---

## 1. Phase Objective

Phase 7A/7B left `/analyze` as a placeholder page. Phase 7C's job was to replace it with a genuinely functional form capable of collecting everything `POST /procurement/analyze` requires and producing the exact request payload — while stopping short of actually sending it. Backend connection is explicitly deferred to Phase 7D.

## 2. Backend Contract Discovery

**Files inspected (authoritative, read directly this session):** `backend/api/schemas.py`, `backend/api/routes/procurement.py`, `backend/models/run_contracts.py`, `backend/models/batch_contracts.py`, `backend/models/contracts.py`, `backend/models/enums.py`, `backend/models/reasons.py`, `backend/services/procurement_run.py`, `frontend/src/api/procurementApi.js`, `frontend/src/api/client.js`, `frontend/src/pages/AnalysisPage.jsx`, `frontend/src/components/`, `frontend/src/config/env.js`, `frontend/src/styles/`.

`backend/api/schemas.py`'s `ProcurementAnalysisRequest` is the primary authority. Its exact shape:

```
ProcurementAnalysisRequest (required)
├── commodity: CommodityParamsRequest (required)
│   ├── commodity_id: str (required)
│   ├── freshness_window_days: Optional[int] = None
│   └── moq_kg: Optional[float] = None
├── context: ProcurementContextRequest (required)
│   ├── commodity_id: str (required)
│   ├── date: str (required)
│   └── wholesale_price: Optional[TaggedPriceRequest] = None
│       ├── value_rs_per_kg: float (required, if present)
│       └── geographic_level: PriceGeographicLevel (required, if present)
├── vendor_submissions: List[VendorSubmissionRequest] (required array)
│   └── each item:
│       ├── vendor_id: str (required)
│       ├── location: TaggedLocationRequest (required)
│       │   ├── status: VendorLocationStatus (required enum)
│       │   ├── lat: Optional[float] = None
│       │   └── lon: Optional[float] = None
│       ├── individual_price_rs_per_kg: Optional[float] = None
│       ├── practical_horizon_days: Optional[int] = None
│       ├── user_provided_q_i: Optional[float] = None
│       ├── diary_records: Optional[List[float]] = None
│       └── peer_q_values: Optional[List[float]] = None
└── config: ConfigParamsRequest (required)
    ├── d_max_km: float (required)
    ├── trader_margin: float (required)
    └── transport_tiers: List[TransportTierRequest] (required array)
        └── each item: { capacity_kg: float, cost_rs: float } (both required)
```

**Enums relevant to user input:** `VendorLocationStatus` (`VENDOR_SPECIFIC_APPROXIMATE` / `LOCALITY_CENTROID_PROXY` / `MISSING`) and `PriceGeographicLevel` (`MANDI_LEVEL` / `DISTRICT_LEVEL_PROXY` / `UNKNOWN_GRANULARITY`) — both are the submitter's own honest declaration of data precision/provenance, so both are real form inputs. **Enums explicitly excluded from the form** (backend-output concepts, per this phase's own rule): `DecisionState` (BUY_TOGETHER/WAIT_OR_EXPAND_GROUP/DO_NOT_BUY_TOGETHER/ABSTAIN — the user never selects a decision), `EstimationProvenance` (not even a request field — it is *derived* by `backend/services/eligibility.py` from which of `user_provided_q_i`/`diary_records`/`peer_q_values` was actually used), `OutcomeKind`, and every reason-code enum in `backend/models/reasons.py` (`ValidationErrorReason`/`AbstentionReason`/`ContextValidationReason` — all backend-computed explanations, never inputs).

**Discrepancy documented, not fixed (per the Authoritative Contract Rule):** the schema carries **two independent** `commodity_id` fields — `commodity.commodity_id` and `context.commodity_id` — with no cross-field validator requiring they match. The backend was not touched to "fix" this. Instead, the form collects **one** `commodityId` value and `buildAnalysisPayload.js` populates both request fields from it (Section 8) — a frontend UX decision, documented in that file's own header comment, not a backend change.

## 3. Form Architecture

```
frontend/src/pages/AnalysisPage.jsx        (renders the workflow intro + <AnalysisForm/>)
frontend/src/components/analysis/
    AnalysisForm.jsx        -- top-level form, composes every section
    FormSection.jsx         -- <fieldset>/<legend> section wrapper (Card-styled)
    FormField.jsx           -- label + control + hint/error wrapper
    VendorForm.jsx           -- one vendor's fields
    TransportTierRow.jsx    -- one transport tier's fields
    RequestPreview.jsx      -- optional dev-only "Request Preview" panel
    useProcurementForm.js   -- the custom hook: single source of truth for all form state
    initialFormState.js      -- state factory functions (no invented domain defaults)
    formNumbers.js           -- empty/zero/null-safe numeric-string parsing helpers
    validateAnalysisForm.js -- Layer-1 structural validation only
    buildAnalysisPayload.js -- pure form-state -> exact API payload converter
```

**Components reused from Phase 7B, unmodified:** `Button`, `Card`, `Badge`, `PageHeader`, `WorkflowSteps`. No duplicate of any of these was created (the components directory was inspected first, per this phase's explicit instruction).

**State architecture:** `useProcurementForm()` owns the entire form as one state object (`formState`), plus `errors` and `preparedPayload`. Every mutation (add/remove/update vendor or transport tier, update a scalar field) goes through one of the hook's exported functions — there is no second copy of the vendor list, commodity data, or config anywhere in the component tree; `AnalysisForm.jsx` and its children only read props and call the hook's callbacks.

## 4. Form Sections

Sections follow the **actual** schema shape rather than the spec's illustrative category names, per its own explicit instruction not to force fields into categories the backend doesn't have:

| Section (UI) | Maps to |
|---|---|
| Procurement Context | one shared `commodityId` (→ both `commodity.commodity_id` and `context.commodity_id`), `context.date`, `context.wholesale_price` |
| Commodity Parameters | `commodity.freshness_window_days`, `commodity.moq_kg` |
| Procurement Configuration | `config.d_max_km`, `config.trader_margin`, dynamic `config.transport_tiers[]` |
| Vendors | dynamic `vendor_submissions[]` — each `VendorForm` card holds ALL of one vendor's fields (location, price, horizon, demand) in one place, since that is how `VendorSubmissionRequest` actually nests them (the backend does not have separate "Vendor Locations" / "Demand Information" top-level arrays) |

## 5. Vendor Management

`useProcurementForm`'s `addVendor()` appends a fresh vendor (via `createInitialVendor()`, a factory giving it a unique internal `localId` for React's `key`/state addressing — distinct from the user-entered `vendor_id` text field, which is free to be edited or even temporarily duplicated while typing). `removeVendor(localId)` filters it out. Vendor identity in the UI is a simple ordinal header ("Vendor 1", "Vendor 2", …) recomputed from array position, per this phase's accessibility requirement.

**Vendor-removal safety (documented choice, purely frontend UX, not a backend rule):** if only one vendor remains, its "Remove Vendor" button is disabled (`canRemove={formState.vendors.length > 1}`), and `removeVendor` itself additionally refuses to drop the array to zero as a second guard. A zero-vendor array is never producible through the UI.

## 6. Validation

**Frontend structural validation (implemented, `validateAnalysisForm.js`):** required-field presence (commodity ID, date, D_max, trader margin, at least one vendor, at least one transport tier), "is this text a well-formed number" for every numeric field, "are these comma-separated values well-formed numbers" for diary/peer lists, and vendor-ID uniqueness (justified in Section 8's code comments: `backend/services/group_formation.py` keys vendors by `vendor_id` in a plain dict, so a duplicate would silently collide rather than being classified — this is request-integrity, not a business rule).

**Explicitly NOT validated here (remains the backend's responsibility):** whether a price or quantity is negative, whether evidence is sufficient for demand estimation, eligibility, geographic compatibility, MOQ/freshness satisfaction, or any decision outcome. `backend/services/validation.py`/`eligibility.py` already classify exactly these cases into `VALIDATION_ERROR`/`ABSTAIN` per vendor without blocking the rest of the batch — duplicating any of it here would prevent a user from ever submitting data that legitimately exercises those backend code paths.

## 7. Numeric and Optional Value Handling

`formNumbers.js` centralizes every numeric-string parse. The critical rule this phase called out explicitly — `Number("")` evaluating to `0` — is handled by checking for an empty/whitespace string **before** any `Number()` call, in every helper:
- `parseRequiredNumber`: empty → a distinct `EMPTY` sentinel (never `0`); the caller then raises a "this field is required" error, never silently defaults it.
- `parseOptionalNumber`: empty → `null` (preserving the backend's real `Optional[float]` semantics); a non-empty unparseable string → a distinct `INVALID` sentinel, never coerced to `0`.
- `parseOptionalNumberList`: empty text → `null`; each comma-separated token is parsed individually, any one unparseable token invalidates the whole field.

**Known simplification, documented:** there is no UI path to submit an explicit empty array `[]` for `diary_records`/`peer_q_values` — an untouched or cleared text field always maps to `null`. No natural user action in a form context would signal "I explicitly assert zero records" differently from "I have not provided this," so this distinction (which exists as a test fixture case in the backend, `VENDOR_EMPTY_DIARY_TUPLE`) is not reachable from this form. This is a frontend UX limitation, not a backend change.

## 8. Payload Preparation

`buildAnalysisPayload(formState)` is a pure function, called only after `validateAnalysisForm` reports `isValid: true`. It performs the exact field-name/nesting/type mapping documented in Section 2, and throws (rather than silently emitting a malformed payload) if it ever encounters unparseable data — since `prepare()` in the hook always validates first, this path should never trigger in normal use, and its presence is a deliberate fail-loudly guard.

Representative example (abbreviated) — a form with one commodity, one vendor with a missing location, and one transport tier:

```json
{
  "commodity": { "commodity_id": "potato", "freshness_window_days": null, "moq_kg": 200 },
  "context": { "commodity_id": "potato", "date": "2026-09-14",
               "wholesale_price": { "value_rs_per_kg": 15.5, "geographic_level": "MANDI_LEVEL" } },
  "vendor_submissions": [
    { "vendor_id": "V2", "location": { "status": "MISSING", "lat": null, "lon": null },
      "individual_price_rs_per_kg": null, "practical_horizon_days": null,
      "user_provided_q_i": null, "diary_records": [8, 9.5, 10], "peer_q_values": null }
  ],
  "config": { "d_max_km": 2.0, "trader_margin": 0.1,
              "transport_tiers": [{ "capacity_kg": 100000, "cost_rs": 800 }] }
}
```

This exact shape (a 2-vendor variant) was independently loaded and validated against the real `backend/api/schemas.py:ProcurementAnalysisRequest` Pydantic model in-process (`ProcurementAnalysisRequest.model_validate(...)`, no HTTP request, no server) — it parsed with **zero validation errors** (Section 12).

## 9. API Boundary

Confirmed explicitly: **no API request is made anywhere in this phase's code.** `analyzeProcurement()` is never imported or called by any new file. `fetch()` does not appear anywhere under `frontend/src/components/analysis/` or in the modified `AnalysisPage.jsx`. `frontend/src/api/client.js` and `frontend/src/api/procurementApi.js` were inspected but **not modified** (confirmed by `git status --short frontend/src/api/` returning no output). Backend integration is deferred to Phase 7D, exactly as instructed.

## 10. Files Created

`frontend/src/components/analysis/{AnalysisForm.jsx, FormField.jsx, FormSection.jsx, VendorForm.jsx, TransportTierRow.jsx, RequestPreview.jsx, useProcurementForm.js, initialFormState.js, formNumbers.js, validateAnalysisForm.js, buildAnalysisPayload.js}` (11 files), `frontend/src/styles/analysis.css`, this report.

## 11. Files Modified

`frontend/src/pages/AnalysisPage.jsx` (placeholder "information this analysis will collect" cards replaced with `<AnalysisForm/>`; the Phase 7B workflow-steps intro section is kept), `frontend/src/main.jsx` (added the `analysis.css` import).

**Not modified, confirmed:** `frontend/src/pages/ResultsPage.jsx`, `frontend/src/pages/HistoryPage.jsx`, `frontend/src/api/client.js`, `frontend/src/api/procurementApi.js`, every file under `backend/`, `requirements.txt`, and every database file.

## 12. Tests and Verification

1. `npm run build` — **PASS** (62 modules transformed, zero errors).
2. `npm run lint` (oxlint) — **PASS**, zero warnings.
3. Dev server route check: `/`, `/analyze`, `/results`, `/history`, `/some-invalid-route` all returned `200` with the correct shell; direct requests for `AnalysisForm.jsx`, `VendorForm.jsx`, `useProcurementForm.js`, and the updated `AnalysisPage.jsx` all transformed cleanly with no `SyntaxError`/`Failed to resolve import`/server-error markers.
4. **Form behavior**, verified by exercising the pure logic modules directly (they have zero React dependency, so this is a faithful, deterministic check of exactly the code the UI calls) via a temporary, since-deleted Node script:
   - Add vendor → count increases; each vendor gets a distinct internal id.
   - Edit one vendor's field → only that vendor's state changes, the other is untouched.
   - Remove vendor → count decreases, remaining vendor's edited value is preserved.
   - `parseOptionalNumber("")` → `null` (not `0`); `parseOptionalNumber("0")` → `0` (real zero preserved); `parseRequiredNumber("")` → a distinct "empty" signal, never silently `0`.
   - Zero vendors → `validateAnalysisForm` reports invalid with a clear message.
   - Duplicate vendor IDs → reported invalid with a clear message.
   - A fully filled, valid form → `validateAnalysisForm` reports valid, and `buildAnalysisPayload` produces the exact nested structure documented in Section 8, field-by-field verified (39/39 checks passed).
5. **Payload structure verification against the actual Pydantic schema (Section 8):** the generated payload was loaded and passed through `ProcurementAnalysisRequest.model_validate(...)` directly in Python — **validated successfully with zero errors**, confirming exact conformance beyond a manual visual comparison.
6. `pytest -q` (backend): **122 passed, 0 failed, 0 skipped** — unchanged.
7. `git status --short backend/ requirements.txt` — no output, confirming zero backend/database changes this phase.

## 13. Problems Found

No blocking problems. One minor, non-blocking technical note: the analysis logic modules use extensionless relative imports (e.g. `from "./formNumbers"`), which Vite resolves natively but plain Node's strict ESM loader does not — encountered only while writing this phase's own temporary Node-based verification script, not a defect in the shipped app (`npm run build`/`npm run lint` were unaffected throughout). Explicit `.js` extensions were added to these imports as a harmless, spec-correct improvement (still fully Vite-compatible), rather than left as a latent inconsistency.

**No blocking problems found.**

## 14. Scope Verification

Explicitly confirmed **not** implemented this phase: any call to `POST /procurement/analyze`, any call to `analyzeProcurement()`, any `fetch()`, any backend file change, any database/SQLite change, authentication, Supabase, Firebase, ML, Results-page API integration, History-page API integration, and no new frontend dependency (`frontend/package.json` unchanged from Phase 7B).

## 15. Recommended Next Phase

**Phase 7D — Frontend-to-Backend Analysis Integration** (connecting this form's prepared payload to `analyzeProcurement()`, handling the loading/success/error states, and routing to a real Results view). Not begun.

---

**Files read for this phase:** `backend/api/schemas.py`, `backend/api/routes/procurement.py`, `backend/models/run_contracts.py`, `backend/models/batch_contracts.py`, `backend/models/contracts.py`, `backend/models/enums.py`, `backend/models/reasons.py`, `backend/services/procurement_run.py`, `frontend/src/api/procurementApi.js`, `frontend/src/api/client.js`, `frontend/src/pages/AnalysisPage.jsx`, `frontend/src/components/` (full listing), `frontend/src/config/env.js`, `frontend/src/styles/`.
**Files created/modified:** see Sections 10–11.
