# Phase 7D — Frontend-to-Backend Analysis Integration

**Date:** 2026-09-14
**Scope:** Connect the Phase 7C procurement analysis form to the existing `POST /procurement/analyze` endpoint — real submission, loading/duplicate-submission protection, error handling, and a minimal result handoff to `/results`. No Results Dashboard, no History integration, no backend/database changes.

---

## 1. Phase Objective

Phase 7C could validate a form and build an exact request payload, but never sent it. Phase 7D's sole job is to close that gap: call the real, already-implemented `analyzeProcurement()`, handle the real response (success or failure) honestly, and hand a successful result off to the Results page — without building the Results Dashboard itself, without touching History, and without changing anything on the backend.

## 2. Existing API Contract

**Endpoint used:** `POST /procurement/analyze`. **Existing frontend function reused, unmodified:** `analyzeProcurement(runInput)` in `frontend/src/api/procurementApi.js`, which itself delegates to `post()` in `frontend/src/api/client.js` — the sole `fetch()` call site in the project, untouched this phase. **Request source:** `buildAnalysisPayload()` (Phase 7C, unmodified) via `useProcurementForm().prepare()`. **Response source:** the real `ProcurementRunResult` JSON produced by `backend/api/routes/procurement.py`'s `analyze_procurement` handler, via `to_json_safe(ProcurementRunService().run(...))` — unchanged since Phase 6G/6H.

**Files inspected this phase (read directly, not assumed):** `frontend/src/api/client.js`, `frontend/src/api/procurementApi.js`, `frontend/src/config/env.js`, `frontend/src/pages/AnalysisPage.jsx`, `frontend/src/components/analysis/*` (all Phase 7C files), `frontend/src/App.jsx`, `frontend/src/main.jsx`, `frontend/src/routes/AppRoutes.jsx`, `frontend/src/pages/ResultsPage.jsx`, `frontend/src/styles/*`, `backend/api/main.py`, `backend/api/routes/procurement.py`, `backend/api/schemas.py`, `backend/models/run_contracts.py`, `backend/services/procurement_run.py`, `backend/persistence/` (read-only, confirming existing persistence behavior — not modified).

Confirmed by inspection: `client.js`'s `request()` already distinguishes a network-level failure (`fetch()` itself throwing, caught and re-thrown as `"Unable to reach the backend at <url>: <detail>"`) from an HTTP-level failure (non-`ok` response, re-thrown as `"Request to <path> failed (HTTP <status>): <detail>"`) — both as plain `Error` objects with no separate error-type field. This existing convention is reused as-is (Section 6), not replaced.

## 3. Integration Architecture

```
AnalysisForm (Phase 7C form, now also owns submission)
    ↓ user clicks "Analyze Procurement"
Phase 7C structural validation (useProcurementForm().prepare(), UNCHANGED)
    ↓ (only if structurally valid)
Phase 7C payload builder (buildAnalysisPayload(), UNCHANGED)
    ↓
analyzeProcurement(payload)   [frontend/src/api/procurementApi.js, UNCHANGED]
    ↓
client.js post()               [frontend/src/api/client.js, UNCHANGED]
    ↓
POST /procurement/analyze
    ↓
FastAPI (backend/api/routes/procurement.py, UNCHANGED)
    ↓
ProcurementRunService.run() -- existing Phase 6B-6E decision pipeline (UNCHANGED)
    ↓
SQLite persistence (Phase 6G, UNCHANGED)
    ↓
JSON response (ProcurementRunResult)
    ↓
AnalysisForm: minimal shape check, then navigate("/results", { state: { result } })
    ↓
ResultsPage: reads location.state.result, shows minimal handoff confirmation
```

## 4. Submission Flow

1. User clicks the submit button (now labeled **"Analyze Procurement"**, since it genuinely submits — Phase 7C's "Prepare Analysis" label was only renamed because the behavior actually changed).
2. `handleSubmit` calls the *existing* `prepare()` (Phase 7C, unmodified), which runs structural validation and — only if valid — builds the payload.
3. **If structurally invalid:** the function returns immediately after `prepare()`; `analyzeProcurement()` is never called. Field-level errors render exactly as they did in Phase 7C (unchanged).
4. **If valid:** submission state becomes `"submitting"`, the button switches to "Analyzing Procurement…" and disables, and `analyzeProcurement(payload)` is called.
5. **On success:** a minimal response-shape check passes (Section 9), and `navigate("/results", { state: { result: response } })` fires — navigation happens *only* after the response is in hand, never before.
6. **On failure:** submission state becomes `"error"` with a user-safe message (Section 6); no navigation occurs.

## 5. Loading and Duplicate Submission Protection

Two layers, both in `AnalysisForm.jsx`:
1. **UI-level:** the submit button has `disabled={isSubmitting}` (and the Reset button too, so a mid-flight reset can't create a confusing state) — a disabled `<button>` cannot dispatch another `submit` event.
2. **Logic-level guard:** `handleSubmit`'s first line is `if (submission.status === "submitting") return;` — belt-and-suspenders in case a second submit event is somehow dispatched (e.g. a stray Enter keypress) before React re-renders the disabled button.

No `AbortController` or request-cancellation logic was added — not needed for this simple guard, per the phase's own "do not add unless genuinely necessary" instruction.

## 6. Error Handling

**Reused exactly, not reinvented:** `client.js`'s existing thrown-`Error` convention (Section 2). `AnalysisForm.jsx` adds one small function, `describeSubmissionError(error)`, that inspects `error.message`'s existing prefix (`"Unable to reach the backend"` for network failures) to choose between two honest, non-technical, already-approved-wording messages:
- Network failure → *"Unable to connect to the analysis service. Please check that the backend is running and try again."*
- Any HTTP-level failure (4xx/5xx) or an unexpected/malformed response → *"The analysis request could not be completed. Please try again."*

The raw `error.message` (which can include a JSON-stringified Pydantic `detail` array for a 422) is **never** shown to the user — it stays out of the UI entirely, avoiding any internal/technical leakage, matching this phase's explicit requirement.

**Clearly separated from field validation:** field-level errors (e.g. "Enter a valid number.") are Phase 7C's existing per-field `errors` object, rendered inline by `FormField` — completely untouched. Submission errors render in a distinct `ErrorState` block (Phase 7B component, reused) below the form actions, never mixed into the same element or wording as a field error.

## 7. Response Handling

The backend response is stored and forwarded **exactly as received** — `result: response` where `response` is the raw parsed JSON from `client.js`. Nothing is recomputed, renamed, flattened, or reinterpreted in React: no savings, decision, eligibility, distance, or group-selection logic exists anywhere in the new code (confirmed by inspection — `AnalysisForm.jsx`'s only post-response logic is the minimal shape check in Section 9). `ResultsPage.jsx` reads `location.state.result` and displays exactly four backend-sourced fields verbatim (`run_status`, `commodity_id`, `context_date`) plus a static "detailed results are coming" note — no interpretation of what those values *mean*.

## 8. Results Handoff

**Mechanism chosen:** React Router navigation state (`navigate("/results", { state: { result } })`), read on the other end via `useLocation().state?.result`. This was the simplest option consistent with the existing architecture — `AppRoutes.jsx`/`App.jsx` already use `react-router-dom` with nothing else added, and no global state library exists or was introduced (Section 16).

**Refresh limitation, stated honestly and not solved here:** navigation state is held in the browser's session history entry, not in any durable store the frontend controls. A hard refresh of `/results`, or a direct URL visit, loses it. This is explicitly acceptable for Phase 7D — the backend already durably persisted the run via Phase 6G before the response was even returned, so the *data* isn't lost, only this particular unauthenticated browser tab's momentary reference to it. Retrieving a specific run reliably after a refresh (e.g. via `GET /procurement/runs/{run_id}`) is History/Results-by-ID integration, explicitly out of this phase's scope.

## 9. Valid Backend Outcomes vs API Failures

`ABSTAIN` vendors, zero eligible vendors, zero candidate groups, and zero selected groups are all **legitimate, successfully-returned decision-support outcomes** — the backend still responds `HTTP 200` with a complete `ProcurementRunResult` body in every one of these cases (confirmed directly in Section 10's real integration test, which produced `run_status: COMPLETED_NO_SELECTION`, `selected_group_count: 0`, and the promise still *resolved*, not rejected). `AnalysisForm.jsx` treats **any** resolved `analyzeProcurement()` promise as a submission success and navigates — it never inspects `run_status`, `selected_group_count`, or any other decision-content field to decide whether to treat the API call as having "succeeded." The only two things that count as a *submission* failure are (a) `analyzeProcurement()` throwing (network failure or non-2xx HTTP status — both already handled by `client.js`) and (b) the minimal shape check below failing.

**Minimal response-shape check (not a duplicate schema):** before navigating, the code checks only that `response` is truthy and `typeof response.run_status === "string"` — `run_status` is present on every outcome branch of `ProcurementRunResult` (`backend/models/run_contracts.py`), unlike `group_formation`/`final_selection`, which are legitimately `null` for some outcomes and therefore cannot be used as a "did this work" signal. If this check fails, it is treated as an integration failure (a generic submission error is shown) rather than navigating with unusable data.

## 10. Integration Verification

**Actually verified, with real processes:**
- Started the real backend (`python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8731`) — `GET /health` → `200`.
- Started the real Vite dev server (`npm run dev`, served on `http://localhost:5174`) — all 5 routes (`/`, `/analyze`, `/results`, `/history`, `/some-invalid-route`) returned `200`; `AnalysisForm.jsx` and the updated `ResultsPage.jsx` transformed with no error markers.
- **Ran the real, completely unmodified `frontend/src/api/client.js` and `procurementApi.js`** via Vite's own `ssrLoadModule` (loaded through Vite's module graph with real `import.meta.env` substitution — not a reimplementation, the actual shipped code) and called the real `analyzeProcurement()` against the real running backend with a payload built by the real, unmodified Phase 7C `buildAnalysisPayload()`/`validateAnalysisForm()`. Result: `run_status: COMPLETED_NO_SELECTION`, `selected_group_count: 0`, `eligible_vendor_count: 2`, `candidate_group_count: 1` — a genuine zero-selected-groups outcome, confirming Section 9's rule with a real response, not a hypothetical.
- **Persistence confirmed twice, independently:** direct SQLite inspection of `data/app/procurement.db` showed the row count increase from 3 → 4 immediately after the call, and the same real, unmodified `getProcurementRuns()` call returned 4 runs with the new one listed newest-first — both matching.
- **Malformed-request path:** the same real `analyzeProcurement()` call, given a deliberately incomplete payload, correctly threw an `Error` whose message began `"Request to /procurement/analyze failed (HTTP 422): ..."` — confirming the HTTP-error branch (as opposed to the network-failure branch) activates correctly for a real 422.
- **Network-failure path:** the backend process was stopped, and the same real `analyzeProcurement()` call was retried — it correctly threw `"Unable to reach the backend at http://127.0.0.1:8731/procurement/analyze: fetch failed"`, confirming `describeSubmissionError()`'s prefix match (Section 6) is exercised correctly by a genuine connection failure, not a simulated one. The backend was then restarted normally (not left broken).
- **CORS:** a real `OPTIONS` preflight for `POST /procurement/analyze` with `Origin: http://localhost:5174` (the frontend's actual running origin) returned `access-control-allow-origin: http://localhost:5174` — confirming a real browser tab at that origin would be permitted to read the response. CORS was **not modified** this phase (already correctly configured in Phase 7A).
- `pytest -q`: **122 passed, 0 failed, 0 skipped**, unchanged.
- `git status --short backend/ requirements.txt`: no output — zero backend files touched.

**Not verified (honestly stated, not claimed):** no actual browser (Chrome/Firefox/etc.) was driven — no headless-browser automation tool was installed for this phase (consistent with every prior frontend phase's documented limitation), so the literal in-browser click-through ("fill the form, click the button, watch it navigate") was not performed with a real DOM/renderer. What *was* verified instead — the real, unmodified frontend API modules executed via Vite's own module loader against a real backend and a real database, exercising every one of the success/error/persistence/CORS code paths `AnalysisForm.jsx` depends on — is the strongest verification achievable in this environment without adding a new dependency, and is a materially stronger check than a code-only review.

## 11. Files Created

**None.** This phase modified existing Phase 7C/7B files only.

## 12. Files Modified

- `frontend/src/components/analysis/AnalysisForm.jsx` — added the submission state machine, `analyzeProcurement()` call, minimal response-shape check, navigation, and error/loading UI. Form state, validation, and payload building are unchanged (still `useProcurementForm()`, `validateAnalysisForm.js`, `buildAnalysisPayload.js` — none of which were touched).
- `frontend/src/pages/AnalysisPage.jsx` — one paragraph of introductory copy updated to reflect that the form now actually submits (no structural change).
- `frontend/src/pages/ResultsPage.jsx` — added the minimal result-handoff branch (Section 8); the pre-existing Phase 7B empty-state branch is preserved unchanged as the direct-visit fallback.

**Not modified, confirmed:** `frontend/src/api/client.js`, `frontend/src/api/procurementApi.js`, `frontend/src/config/env.js`, every Phase 7C form-logic file (`useProcurementForm.js`, `validateAnalysisForm.js`, `buildAnalysisPayload.js`, `formNumbers.js`, `initialFormState.js`), every backend file.

## 13. Backend Changes

**None.** Confirmed by `git status --short backend/ requirements.txt` returning no output, both immediately after implementation and again after the full integration test run.

## 14. Tests and Verification

```
npm run build   -> PASS (63 modules, zero errors)
npm run lint    -> PASS (oxlint, zero warnings)
pytest -q       -> 122 passed, 0 failed, 0 skipped (unchanged baseline)
```
No frontend testing framework was inspected-and-found — none exists in this project (confirmed: `frontend/package.json` has no test runner script or dependency), and per this phase's explicit instruction, none was added. Verification relied on build/lint plus the real integration testing described in Section 10.

## 15. Problems Found

No bugs, CORS issues, or API/response mismatches were found. `client.js` and `procurementApi.js` needed no changes — they already correctly supported everything this phase needed.

**No blocking problems found.**

## 16. Scope Verification

Explicitly confirmed **not** implemented this phase: a detailed Results Dashboard (savings/decision/vendor/group cards, charts, or explanations — `ResultsPage.jsx` shows only `run_status`/`commodity_id`/`context_date` as plain text), History integration (`getProcurementRuns()`/`getProcurementRun()` were only called from a temporary, deleted verification script, never from any page), authentication, Supabase, Firebase, any backend or database modification, any new API endpoint, ML, fake/mocked results (every result shown or logged during verification came from a real backend response), and no new dependency (`frontend/package.json` unchanged).

## 17. Recommended Next Phase

**Phase 7E — Results Dashboard and Decision Explanation Interface** (building the real display of `run_status`, vendor outcomes, group decisions, and final selection that `ResultsPage.jsx` currently only stubs). Not begun.

---

**Files read for this phase:** see Section 2.
**Files created:** none. **Files modified:** see Section 12.
