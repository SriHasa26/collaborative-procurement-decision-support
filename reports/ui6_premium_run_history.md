# UI-6 — Premium Procurement Run History

**Date:** 2026-09-16

## 1. Objective

Redesign `/history` (and only `/history`) into a premium "Procurement Run History / Activity Center": a page where a user can scan previous analyses at a glance, find a specific run via search/filter, see its real decision/savings/vendor outcome, and reopen it into the UI-5 Decision Cockpit — with every displayed value grounded in the actual API response, never invented.

## 2. Existing History Architecture Inspected

Read in full before writing anything: `pages/HistoryPage.jsx` (Phase 7F), `components/history/RunHistoryTable.jsx`, `components/history/historyHelpers.js`, `api/procurementApi.js`, `api/client.js` (to confirm exactly how requests/auth headers are built), `pages/ResultsPage.jsx` and `components/results/resultHelpers.js`/`runStatusMeta.js`/`decisionStateMeta.js` (UI-5), `routes/AppRoutes.jsx` (to confirm `/history`'s exact `ProtectedRoute` wrapping), and `components/dashboard/{useDashboardData.js,dashboardMetrics.js,RecentAnalyses.jsx}` (UI-3) — the closest existing precedent for "enriching a lightweight run list with real per-run detail," which this phase's own brief explicitly invited reusing (Rule 3/25: "If richer data requires existing detail requests already supported by the frontend, determine whether that pattern can be reused safely").

## 3. Actual History API Contract

Confirmed directly from source, not assumed:
- `GET /procurement/runs` (`backend/api/routes/procurement.py:list_runs`) calls `repository.list_runs(current_user.user_id)` with **no limit argument** — it returns **every** run the user has, newest-first (`ORDER BY created_at DESC, run_id DESC`, confirmed in both `sqlite_repository.py` and `supabase_repository.py`). **There is no backend pagination of any kind on this endpoint.**
- Each row is `RunSummary` (`backend/persistence/repository.py`): **exactly** `{run_id, created_at, commodity, run_status}` — no savings, no vendor count, no decision state. Its own docstring calls this "lightweight run history only... never input_json/result_json."
- `GET /procurement/runs/{run_id}` (unchanged) returns the full `{run_id, created_at, commodity, run_status, input, result}` — the same shape History's "View Results" flow has used since Phase 7F.
- The real, live database currently contains exactly **1** run for the test account (verified by a direct, read-only query against the real `procurement_runs` table): `POTATO_HYD_2026_09`, `COMPLETED`.

## 4. Data Fields Available

| Source | Fields | Availability |
|---|---|---|
| `GET /procurement/runs` (list) | `run_id`, `created_at`, `commodity`, `run_status` | Always, for every run, unbounded |
| `GET /procurement/runs/{id}` (detail) | full `ProcurementRunResult` — `total_vendors_submitted`, `final_selection.selected_results[].final_decision_state`, `final_selection.total_savings_rs`, `input.vendor_submissions[].vendor_id`, etc. | Only for a run whose detail is actually fetched |

Since the list endpoint alone cannot show a decision, savings figure, or vendor count, and the backend has no way to return that per-row without a new endpoint (explicitly forbidden this phase), History fetches full detail for its most recent `HISTORY_DETAIL_FETCH_LIMIT` (30) runs — the same bounded-enrichment pattern UI-3's `useDashboardData.js` already established and safely uses today, reused rather than reinvented (`components/history/useHistoryData.js`). This does not add a new endpoint, new filtering, or new ownership logic — it is the existing, already-authorized `GET /procurement/runs/{run_id}` called once per run, exactly as `HistoryPage.jsx`'s own "View Results" click has always done.

## 5. Data Mapping into UI

| Field | UI element |
|---|---|
| `run.commodity` | Row title |
| `run.created_at` | Row timestamp (`historyHelpers.formatRunTimestamp`, unchanged) |
| `run.run_id` | Subtly shown technical metadata (`historyHelpers.shortenRunId`, unchanged) — only ever the real ID, never fabricated |
| `run.run_status` | Fallback badge (`runStatusMeta.getRunStatusMeta`, unchanged) when no group was selected |
| `detail.result.final_selection.selected_results[0].final_decision_state` | `DecisionStateBadge` (real decision, only when detail is loaded and a group was actually selected) — via the new `getPrimaryDecisionState()` helper |
| `detail.result.total_vendors_submitted` | "Vendors" metric, or "—" |
| `detail.result.final_selection.total_savings_rs` | "Expected savings" (currency-formatted, `resultHelpers.formatCurrency`, unchanged), or "—" |
| Overall `entries.length` from the list call | "Total runs" (History Overview) — always the true, complete count, unaffected by the enrichment cap |
| `entries[0]` | "Most recent" (History Overview) |
| `detail.input.vendor_submissions[].vendor_id` | Vendor-ID search matching |

No field is invented: a run whose detail was not fetched (beyond the cap, or a failed individual fetch) shows "Completed"/its real `run_status` badge, "—" for vendors and savings, and an explicit "Full detail not loaded for this run yet." note — never a guess.

## 6. Components Created

`frontend/src/components/history/{useHistoryData.js, historyFilters.js, HistoryOverview.jsx, HistoryToolbar.jsx, RunHistoryRow.jsx, RunHistoryList.jsx, HistorySkeleton.jsx}`, `frontend/src/styles/history.css`.

## 7. Components Modified

`pages/HistoryPage.jsx` (full rewrite as a thin orchestrator), `main.jsx` (added the `history.css` import, matching the existing per-page-stylesheet convention), `components/results/resultHelpers.js` (one small additive export, `getPrimaryDecisionState(result)` — extracts the exact "primary decision" derivation `DecisionHero.jsx` (UI-5) already computes inline, so History does not re-derive the same rule a second time; `DecisionHero.jsx` itself was **not** touched, per this phase's "do not redesign Results" rule).

Also first real adoption of UI-1's previously-unused `components/ui/Input.jsx`/`Select.jsx` primitives (the search box and decision-filter dropdown) — they existed since UI-1 specifically for "a future page," and no phase had used them until now.

## 8. Components Deleted

`components/history/RunHistoryTable.jsx` — its one caller (`HistoryPage.jsx`) was rewritten to use `RunHistoryList`/`RunHistoryRow` instead; confirmed via grep that no other file imported it before deletion. The `.history-table`/`.history-table-wrapper` CSS classes it used are **not** dead — they are still used by `results/AllocationTable.jsx`/`VendorOutcomesTable.jsx` (UI-5) and were left untouched.

## 9. Search/Filter Behavior

Both are entirely client-side, over the already-fetched (unbounded) run list — no backend search/filter endpoint was created, per this phase's explicit prohibition.
- **Search** matches commodity (always available), run ID (always available), and vendor ID (only for a run whose detail was fetched — `input.vendor_submissions`, the complete as-submitted vendor list, not just the eligible subset).
- **Decision filter** offers the four real `DecisionState` values (`BUY_TOGETHER`/`WAIT_OR_EXPAND_GROUP`/`DO_NOT_BUY_TOGETHER`/`ABSTAIN`, from the same exhaustive `decisionStateMeta.js` list UI-5 already uses) plus one clearly-distinct, non-`DecisionState` option, "No group selected," for runs whose `run_status`-driven fallback applies. A run with no fetched detail matches no specific decision filter (its true decision is genuinely unknown) but still appears under "All decisions."
- **Clear Filters** appears only when a search term or a non-"All" filter is active, and resets both. A distinct "No matching procurement runs" empty state (with its own Clear Filters action) is shown when filters produce zero results — never confused with the true "no runs exist at all" empty state, which is handled earlier in `HistoryPage.jsx` before any toolbar is even rendered.

## 10. Responsive Behavior

Verified at 1440px/1024px/390px (Section 18). The toolbar's two fields wrap to full-width below 640px; each run row is a flex-wrapping card that reflows from a single wide line (desktop) to a stacked card (mobile) with no forced horizontal table; the "View Decision" action always remains visible and directly tappable — never hover-only.

## 11. Accessibility

Search input and decision `<select>` both have real (visually-hidden, `.sr-only`) `<label>`s; each run row is one genuine `<button>` (full keyboard operability with no custom key handling needed) with a descriptive `aria-label` naming the commodity and date; decision meaning is carried by both the badge's label text and its icon, never color alone (reusing `DecisionStateBadge`/`Badge` unchanged); focus-visible styling is inherited from the existing `.card-interactive` treatment (UI-1).

## 12. Loading / Error / Empty States

- **Loading:** `HistorySkeleton.jsx`, reusing UI-3's existing `.skeleton-block` shimmer (no second shimmer implementation) — respects `prefers-reduced-motion` via the same global rule every prior UI phase has relied on.
- **Error:** a safe, generic message ("Unable to load procurement history") with **Retry** and a new **Back to Dashboard** action (a legitimate, already-existing route) — never a raw exception, stack trace, or backend detail string. Verified: the underlying `Error: simulated network failure` text never reaches the rendered page (Section 18).
- **Empty (no runs at all):** unchanged copy/intent from Phase 7F, restyled — "No procurement runs yet" + "Start Your First Analysis".
- **Empty (search/filter, runs exist):** the distinct "No matching procurement runs" state (Section 9).

## 13. History → Results Navigation

Preserved and slightly optimized, never changed in contract: clicking a row whose detail was already fetched by `useHistoryData.js` navigates directly with that already-in-memory data (avoiding a redundant network round-trip for the common case); a row beyond the enrichment cap (or whose detail fetch failed) falls back to the **exact, unchanged** Phase 7F/UI-5 on-demand `getProcurementRun` fetch before navigating. Both paths call `navigate("/results", { state: { result, runId, createdAt } })` — byte-for-byte the same shape UI-5's `ResultsPage.jsx` already expects; `ResultsPage.jsx` itself was not touched.

## 14. Real-Data Verification

The real, previously-persisted `POTATO_HYD_2026_09` run (fetched read-only from the live database in an earlier phase, matching the row confirmed live in Section 3) was used as one of the fixtures in a real-browser verification harness (Section 18). Confirmed rendered correctly by the actual, unmodified `HistoryPage`/`RunHistoryRow`/`useHistoryData`/`historyFilters` code: commodity `POTATO_HYD_2026_09`, 4 vendors, `Buy Together` decision badge, `₹3,732.60` expected savings, and a working "View Decision" action — matching the reference values in this phase's own brief exactly, without any of them being hardcoded anywhere in the new code (confirmed by inspection: every one of these values is read from the fixture's `result` object at render time, the same code path a real API response would take).

## 15. Build Result

`npm run build` — **172 modules transformed, 0 errors** (up from 163 before this phase, reflecting the 7 new History files).

## 16. Lint Result

`npm run lint` (oxlint) — **0 warnings**.

## 17. Backend Test Result

`python -m pytest -q` — **178 passed, 0 failed, 0 skipped** (unchanged from before this phase — confirms the backend was genuinely never touched).

## 18. Browser Verification

No real Supabase session was available, and none was fabricated. Two complementary real-Chromium techniques were used:

**A. Unauthenticated structural checks** against the real production `vite preview` build: `/history`, `/results`, `/analyze`, `/dashboard` all correctly redirect an unauthenticated visitor to `/signin` (confirmed with fresh pages and adequate wait time, after an initial rushed multi-route check produced one false-negative timing artifact that was investigated and resolved by re-testing in isolation — documented honestly rather than silently discarded); `/` still loads. **5/5 passed.**

**B. Full real-and-synthetic-data rendering** — the most important verification, since redirect checks alone say nothing about whether the new page actually works. A temporary, self-contained harness (`harness.html` + `_harness_main.jsx` + `_harness_fixtures.js`, all under `frontend/`, never imported by `index.html`/`main.jsx`/any route, and **deleted before this report was written** — confirmed via `git status`, which shows no such files) rendered the real, completely unmodified `HistoryPage.jsx` inside a `MemoryRouter` (the same technique UI-5's own harness used to bypass `ProtectedRoute`, which requires a real session this environment lacks). Because `HistoryPage` actively calls the real API client, `window.fetch` was intercepted at the browser network layer to serve canned responses — the real `POTATO_HYD_2026_09` run plus a small number of clearly-synthetic fixtures (never presented as real; used only to exercise decision-badge variety, the "no selection" fallback, and the enrichment-cap boundary) — so the real, unmodified `useHistoryData.js`/`historyFilters.js`/every new component ran their actual logic against realistic HTTP responses.

Checked at 1440px/1024px/390px: page load, header, both real and synthetic run rows rendering with correct decision badges/vendor counts/savings, search by commodity, search by vendor ID, search-empty state, Clear Filters, decision filter (both a real `DecisionState` value and the "No group selected" option), keyboard-focus reachability, no console errors, no horizontal overflow. Separately verified: the empty-history state, the error state (confirming the raw `simulated network failure` message never reaches the rendered page — only the safe, generic wording does), and a 34-run "many runs" scenario confirming the true total (34) is always shown correctly in the History Overview even though only the first 30 are enriched, with the 32 unenriched entries each honestly showing "—" and a "Full detail not loaded for this run yet." note rather than a fabricated value. **48/48 checks passed.** One real visual defect was found and fixed during this process: the "—" placeholder for a run with no savings was rendering in the success/green color; it now uses the muted text color like every other unavailable value.

**Not verified:** an actual authenticated click-through (sign in → Dashboard → History → open a persisted run → Results) in the live deployed app — this requires a real Supabase session this environment does not have, and none was fabricated to claim otherwise.

## 19. Limitations

- **Authenticated History → Results verification could not be completed because no real Supabase session was available.** The mitigating verification performed instead (Section 18B) exercises the real, unmodified component tree and the real navigation-state hand-off shape against realistic data; the residual risk is narrow (primarily whether `ProtectedRoute`/`AuthContext`, both untouched this phase, still gate correctly — separately confirmed in Section 18A).
- The backend has no pagination on `GET /procurement/runs` (Section 3) — History therefore always fetches the user's **entire** run list on every load, and enriches only the most recent 30 with full decision/savings/vendor detail. For a user with more than 30 runs, older entries remain visible (correct commodity/date/status) but show "—" for decision/vendor count/savings until reopened directly. This is a genuine, documented scope boundary of the frozen backend, not an oversight — implementing a real fix would require backend pagination or a batched detail endpoint, both out of this phase's scope.
- Search over vendor IDs only works for a run whose detail was actually fetched (the same 30-run cap) — a vendor ID belonging only to an unenriched older run will not be found. This is stated plainly in this report rather than silently accepted.

## 20. Backend Confirmation

**Backend NOT modified. Procurement engine NOT modified. Authentication/RLS/JWT NOT modified.** Confirmed by `git status`: zero changes under `backend/` or `supabase/` beyond what was already present from prior phases before this session began. `python -m pytest -q` remains 178 passed / 0 failed / 0 skipped. No new backend endpoint, database column, table, or migration was created; `GET /procurement/runs` and `GET /procurement/runs/{run_id}` are byte-for-byte the same handlers as before this phase.

---

## UI-6 IMPLEMENTATION SUMMARY

**What changed:** `/history` is now a premium Procurement Run History / Activity Center — a History Overview (real total-run-count + most-recent-run facts), a search + decision-filter toolbar, and a polished, keyboard-accessible run list where each row shows the run's real decision (via `DecisionStateBadge`), vendor count, and expected savings whenever that run's detail has been fetched, with an honest "—" and explanatory note otherwise.

**Files created:**
`frontend/src/components/history/useHistoryData.js`, `historyFilters.js`, `HistoryOverview.jsx`, `HistoryToolbar.jsx`, `RunHistoryRow.jsx`, `RunHistoryList.jsx`, `HistorySkeleton.jsx`, `frontend/src/styles/history.css`.

**Files modified:**
`frontend/src/pages/HistoryPage.jsx` (full rewrite), `frontend/src/main.jsx` (one new CSS import), `frontend/src/components/results/resultHelpers.js` (one additive export, `getPrimaryDecisionState`).

**Files deleted:**
`frontend/src/components/history/RunHistoryTable.jsx` (superseded; confirmed single caller before removal).

**Backend changed:** NO
**Procurement engine changed:** NO
**Authentication/security changed:** NO

**Backend tests:** 178 passed, 0 failed, 0 skipped.
**Build:** clean, 172 modules, 0 errors.
**Lint:** clean, 0 warnings.
**Browser verification:** 5/5 unauthenticated redirect checks + 48/48 checks from a real-Chromium harness rendering the actual unmodified page against real + clearly-synthetic fixture data (search, filters, decision badges, empty/error/many-run states, keyboard access) — one real bug found and fixed (a "—" incorrectly rendered in the success color).
**Real persisted run verification:** the real `POTATO_HYD_2026_09` run rendered with its correct commodity, 4 vendors, `Buy Together` decision, and `₹3,732.60` expected savings — matching this phase's own reference values exactly, none hardcoded.
**Authenticated verification:** not possible in this environment — no real Supabase session was available, and none was fabricated; documented explicitly above.
**Limitations:** no backend pagination exists, so detail-enrichment (and therefore decision/savings/vendor-count display and vendor-ID search) is bounded to the 30 most recent runs; older runs still display correctly with their real summary fields and an honest "—" for anything requiring full detail.

**Report:** `reports/ui6_premium_run_history.md`

**Git operations:** NONE
