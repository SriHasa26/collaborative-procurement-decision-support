# Phase 7F — Procurement Run History & Run Detail Integration

**Date:** 2026-09-14
**Scope:** Implement a real Run History experience — load run metadata from the backend, let the user select a previously stored run, retrieve its complete result, and display it using the existing (Phase 7E) Results Dashboard. No backend changes, no new Results UI, no authentication.

---

## 1. Phase Objective

Phase 7E built a complete Results Dashboard for a freshly-submitted analysis, but `HistoryPage` still showed a static empty table. Phase 7F's job is to make History real: load `GET /procurement/runs`, let the user pick a run, fetch its full stored result via `GET /procurement/runs/{run_id}`, and route it into the *same* dashboard Phase 7E already built — never a second copy of it.

## 2. Existing API Endpoints Reused

`getProcurementRuns()` and `getProcurementRun(runId)` from `frontend/src/api/procurementApi.js` — both already implemented (Phase 7A), both reused completely unmodified. No new `fetch()` call site was added anywhere; `frontend/src/api/client.js` remains the sole one, confirmed by inspection and by `git status` showing neither file touched this phase.

## 3. Exact Real Response Shapes Discovered

Inspected `backend/api/routes/procurement.py`'s `list_runs`/`get_run` handlers and `backend/persistence/repository.py`'s `RunSummary`/`StoredRun` dataclasses, **then confirmed against the real running backend and its already-persisted SQLite data** (no fake rows were inserted — the existing rows from Phase 7D/7E's own testing were reused, per Part 25).

**`GET /procurement/runs`** → a JSON array, each entry **exactly**:
```json
{ "run_id": "...", "created_at": "2026-09-14T13:00:13.891461+00:00", "commodity": "onion", "run_status": "COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS" }
```
No `eligible_vendor_count`, `candidate_group_count`, `selected_group_count`, or any other field is present at this level — confirmed by direct inspection of a real response, not assumed. This is the deliberately lightweight shape Part 3 describes; the History table therefore displays only `run_id`, `created_at`, `commodity`, `run_status` and nothing else.

**`GET /procurement/runs/{run_id}`** → confirmed to match Part 9's example structure closely, but verified rather than assumed:
```json
{
  "run_id": "...", "created_at": "...", "commodity": "...", "run_status": "...",
  "input": { "commodity": {...}, "context": {...}, "vendor_submissions": [...], "config": {...} },
  "result": { "run_status": "...", "commodity_id": "...", "...", "batch_eligibility": {...}, "group_formation": {...|null}, "final_selection": {...|null} }
}
```
**`result` is the exact same `ProcurementRunResult` shape** already produced by `POST /procurement/analyze` and already consumed by `ResultsPage` since Phase 7D/7E — confirmed directly (`stored.result.run_status`, `"batch_eligibility" in stored.result`, etc., verified against a real response). `HistoryPage` therefore extracts `stored.result` (never the whole wrapper, never `stored.input`) before handing it to `/results`.

Also confirmed live: an unknown `run_id` → `404` with `{"detail": "procurement run not found: <id>"}` — the same clean error shape Phase 6G/6H already established, reused unchanged by `client.js`'s existing error handling.

## 4. History Page Behavior

`HistoryPage.jsx` now owns two independent pieces of state: `load` (the run-list fetch: `loading`/`error`/`success`) and `selection` (one run's detail fetch, triggered by "View Results": `idle`/`loading`/`error`). The list loads once on mount via `useEffect`; a `handleViewResults(runId)` function drives the second fetch and the eventual navigation.

## 5. Loading Behavior

List loading: the existing `LoadingState` component ("Loading run history…"). Run-detail loading: the specific row's "View Results" button becomes "Loading…" (`aria-busy`), and **every** button in the table is disabled while any selection is in flight — a duplicate-click guard, matching the same pattern `AnalysisForm.jsx` already established in Phase 7D (disable during the in-flight request).

## 6. Empty Behavior

If `getProcurementRuns()` resolves to an empty array, the existing `EmptyState` component renders ("No procurement runs yet" + a CTA to `/analyze`) — unchanged in wording from Phase 7B's original placeholder, now reached through a real, verified code path instead of being the only possible state.

## 7. Error Behavior

Two independent error surfaces, both using the existing `ErrorState` component with non-technical wording (never a raw stack trace or `error.message` shown verbatim):
- **List-load failure**: a page-level `ErrorState` with a "Retry" button that re-triggers the fetch — the user is never stuck.
- **Run-detail-retrieval failure**: a smaller `ErrorState` shown above the (still-intact) history table — the user remains able to browse and try a different run, or the same one again; the page never redirects to a broken `/results`.

Both reuse the same message-selection technique Phase 7D introduced (`AnalysisForm.jsx`'s `describeSubmissionError`): inspecting `client.js`'s own existing error-message prefix (`"Unable to reach the backend"`) to distinguish a network failure from an HTTP failure, plus one additional case here (an `HTTP 404` substring) for "this run could not be found." No new error architecture was invented.

## 8. History Metadata Displayed

Exactly the four fields `GET /procurement/runs` returns: a shortened Run ID (`Run #5d9f2b71`, with the full `run_id` still present in the row's `title` attribute and used unmodified for the API call), a formatted timestamp, the commodity, and a `run_status` badge. Nothing else is shown or fabricated.

## 9. Run Selection Flow

Each row has a real `<button>` labeled "View Results" (not a link, since it triggers an async fetch before navigating). Clicking it calls `getProcurementRun(run_id)` — never reuses the lightweight list-row data as a substitute for the full stored run, per Part 6's explicit instruction.

## 10. Run Detail Retrieval

On success, a minimal shape check (`stored?.result && typeof stored.result.run_status === "string"`) mirrors the same check `AnalysisForm.jsx` already performs on a fresh analysis response (Phase 7D Section 9) — proof the response is usable before navigating, not a duplicate schema. Only then does `navigate("/results", { state: { result: stored.result } })` fire — the same mechanism, and the same `/results` route, Phase 7D already established for a freshly-computed result. No new route was created.

## 11. ResultsPage Reuse Strategy

**No change was made to `ResultsPage.jsx` or any component under `frontend/src/components/results/` this phase.** `ResultsPage` already reads `location.state.result` and renders the full dashboard from it (Phase 7E) — it has no way to know, and does not need to know, whether that object arrived from a fresh `POST /procurement/analyze` or from `GET /procurement/runs/{run_id}`'s `.result` field, because both are the exact same `ProcurementRunResult` shape (Section 3). This was the intended design already, confirmed rather than assumed.

## 12. Confirmation: No Results Dashboard Duplication Occurred

Confirmed by inspection: no new file named anything like `OldResultsPage`, `RunDetailDashboard`, or `HistoryResultsDashboard` was created; `frontend/src/pages/ResultsPage.jsx`'s `git diff` against the pre-Phase-7F state is empty (it was not touched); every one of Phase 7E's 10 result components remains the sole implementation of the results presentation.

## 13. Date Formatting Behavior

`historyHelpers.js`'s `formatRunTimestamp(createdAt)` parses the backend's ISO-8601 string with `new Date(...)` and formats it via `Intl.DateTimeFormat("en-IN", {...})` (e.g. `14 Sept 2026, 06:30 pm`) — purely a display transformation; the original `created_at` string is never mutated or re-sent anywhere. An unparseable value (`Number.isNaN(date.getTime())`) falls back to showing the raw string rather than inventing a placeholder date, and a missing value shows `—`. Verified against both a real backend timestamp and deliberately invalid input (`null`, `"not-a-date"`).

## 14. Run Status Presentation Behavior

Reuses `frontend/src/components/results/runStatusMeta.js` (Phase 7E's already-existing, already-reviewed `RunStatus` label/color mapping) directly — **no second mapping was created**, and no run status is inferred from `selected_group_count`, `eligible_vendor_count`, savings, or any other field; the backend's own `run_status` string is looked up as-is. This directly satisfies Part 5's explicit instruction and additionally avoids the duplication a new `HistoryRunStatusBadge.jsx` would have introduced.

## 15. Files Created

`frontend/src/components/history/historyHelpers.js`, `frontend/src/components/history/RunHistoryTable.jsx`, this report.

**Deliberately not created:** `HistoryRunStatusBadge.jsx` (Section 14 — the existing `results/runStatusMeta.js` + `Badge` already cover this exactly), `RunHistoryRow.jsx` (a table row is simple enough to inline in `RunHistoryTable.jsx`'s `.map()`, matching the precedent already set by Phase 7E's `GroupDecisionList`/`VendorOutcomesTable`), and `frontend/src/styles/history.css` (no history-specific styling was needed beyond what `components.css`'s existing `.history-table`/`.btn`/`.badge` classes already provide).

## 16. Files Modified

`frontend/src/pages/HistoryPage.jsx` (full rewrite: real data loading/selection/navigation replaces the Phase 7B static placeholder), `frontend/src/styles/global.css` (added one small, genuinely reusable `.sr-only` utility class for the history table's visually-hidden "Actions" column header — the only new CSS this phase needed).

**Not modified, confirmed:** `frontend/src/api/client.js`, `frontend/src/api/procurementApi.js`, `frontend/src/pages/ResultsPage.jsx`, every file under `frontend/src/components/results/`, every backend file.

## 17. Dependencies Added

**None.** `frontend/package.json` is unchanged. Data fetching uses React's own `useState`/`useEffect`/`useCallback` — no React Query, SWR, Redux, or Zustand.

## 18. Build Result

```
npm run build -> PASS (76 modules transformed, zero errors)
```

## 19. Lint Result

```
npm run lint (oxlint) -> PASS, zero warnings
```
One warning was found and fixed during development: an unnecessary synchronous `setState` inside the run-list-loading effect (redundant, since the initial `useState` value was already `"loading"`) — fixed the same way an identical Phase 7B warning was fixed, by moving the "reset to loading" state change into the Retry button's own click handler (a real user event) rather than the effect.

## 20. Backend Test Result

```
pytest -q -> 122 passed, 0 failed, 0 skipped
```
Unchanged from the pre-Phase-7F baseline.

## 21. Real API Integration Result

**Actually verified**, using the same Vite `ssrLoadModule` technique validated in Phases 7D/7E (running the real, unmodified `procurementApi.js` and the real, unmodified new `historyHelpers.js` against a real running backend and its real, pre-existing SQLite data):

- `GET /procurement/runs` → real array of 6 runs, exact shape confirmed (Section 3).
- `formatRunTimestamp`/`shortenRunId` exercised against real data and against `null`/invalid input — all handled safely.
- `GET /procurement/runs/{run_id}` for a real stored run → `stored.run_id` matched the request, `stored.result.run_status` was a real string, `"batch_eligibility" in stored.result` was `true` — exactly what `ResultsPage` needs.
- Simulated `HistoryPage.handleViewResults`'s own usability check against this real response → `true` (would navigate).
- `GET /procurement/runs/{unknown-id}` → correctly threw an `HTTP 404` error; `describeRunRetrievalError` correctly produced "This run could not be found. It may have been removed."
- **Database confirmed read-only**: row count was `6` before and after every one of the above GET calls — no fake data was inserted, no run was created by browsing history (Part 25).
- **Network-failure path**: backend stopped, `getProcurementRuns()` correctly threw `"Unable to reach the backend at .../procurement/runs: fetch failed"`; `describeHistoryLoadError` correctly produced the friendly network-down message; backend restarted normally afterward.
- **CORS**: a real `GET /procurement/runs` request with `Origin: http://localhost:5174` (the frontend's actual running origin) returned `access-control-allow-origin: http://localhost:5174` — unchanged from Phase 7A/7D, not modified this phase.
- Vite dev server: all 5 routes returned `200`; `HistoryPage.jsx`, `RunHistoryTable.jsx`, and `historyHelpers.js` all transformed with no error markers.
- Both dev processes were stopped cleanly after verification.

**Not verified:** no literal browser DOM click-through (no headless-browser tool installed — the same documented limitation as every prior frontend phase). The verification above exercises the exact same API modules and the exact same data every component reads, which is the strongest available alternative in this environment.

## 22. Bugs Found

One lint-level issue (Section 19), fixed before final verification. No backend issues, no API contract mismatches, no response-shape surprises — the actual `GET /procurement/runs/{run_id}` shape matched Part 9's own illustrative example closely once verified against the real code and a real response.

**No blocking problems found.**

## 23. Limitations

Same as Phase 7E: no literal browser-rendered verification was performed. The history list currently has no pagination — `list_runs()` (`backend/persistence/repository.py`) already supports an optional `limit` parameter, but the existing `GET /procurement/runs` route does not expose it as a query parameter, so the frontend cannot request a bounded page; this was not treated as a blocking backend issue (Part 20) since the six existing rows render correctly and pagination was not required by this phase's scope — noted here as a known limitation for a future phase if run history grows large. Duplicate-click protection disables every row's button while any one selection is in flight, rather than only the clicked row — a deliberate simplicity choice (mirroring `AnalysisForm.jsx`'s same pattern), not a limitation of correctness.

## 24. Confirmation: Backend Was Not Modified

Confirmed. `git status --short backend/ requirements.txt` returned no output, both immediately after implementation and again after the full integration test run. No blocking backend issue was discovered — the existing endpoints already supported everything this phase needed.

## 25. Confirmation: Phase 7G+ Was Not Started

Confirmed. No authentication, no Supabase, no Firebase, no database migration, no user accounts, no deployment configuration, and no unrequested frontend redesign. `ResultsPage.jsx` and every Phase 7E results component remain exactly as Phase 7E left them.

---

**Files read for this phase:** `backend/api/routes/procurement.py`, `backend/persistence/repository.py`, `backend/persistence/database.py`, `frontend/src/api/procurementApi.js`, `frontend/src/api/client.js`, `frontend/src/pages/HistoryPage.jsx`, `frontend/src/pages/ResultsPage.jsx`, `frontend/src/components/results/*`, plus a live inspection of the real running backend's responses.
**Files created:** see Section 15. **Files modified:** see Section 16.
