# UI-3 — Premium Procurement Intelligence Dashboard

**Date:** 2026-09-15

## 1. Objective

Build a real, authenticated procurement intelligence dashboard at `/dashboard` that answers "what happened, how much value was generated, what decisions were made, what's next" — using only real, authenticated-user data through the existing API, with no backend change, no fake statistics, and no fabricated activity.

## 2. Existing Dashboard / Route Architecture Inspected

Before writing anything: `frontend/src/routes/AppRoutes.jsx`, `AppLayout.jsx`, `Sidebar.jsx`, `TopBar.jsx`, `auth/useAuth.js`, `api/procurementApi.js`, and — critically — the **actual backend contracts**, read directly from source rather than assumed: `backend/models/run_contracts.py` (`ProcurementRunResult`'s real field names), `backend/models/decision_contracts.py` (`FinalSelectionResult`/`EvaluatedGroupResult`), `backend/models/group_formation_contracts.py`, and the existing frontend helpers that already consume them (`results/resultHelpers.js`, `results/SavingsSummary.jsx`, `history/historyHelpers.js`, `results/runStatusMeta.js`). No route or component was found dedicated to a "dashboard" — the closest prior concept was `HomePage.jsx`, which UI-2 already turned into the public landing page.

**Confirmed exact response shapes** (not assumed): `GET /procurement/runs` returns `RunSummary[]` — `{run_id, created_at, commodity, run_status}` only, no savings/vendor/decision data. `GET /procurement/runs/{run_id}` returns `{run_id, created_at, commodity, run_status, input, result}`, where `result.final_selection` (nullable) carries `total_savings_rs`, `total_vendor_coverage`, `selected_results[].vendor_ids`, `selected_results[].final_decision_state`, and `all_evaluated_results[]` for every candidate group's own decision state.

## 3. Route Strategy

`/dashboard` was added, protected by the **same, unmodified** `ProtectedRoute` and rendered inside the **same, unmodified** `AppLayout` that `/analyze`/`/results`/`/history` already use — no second authentication mechanism, no new layout component beyond the page's own content. `/` (UI-2's public landing page) is completely untouched. `SignInPage.jsx`/`SignUpPage.jsx` now default to redirecting a freshly-authenticated user to `/dashboard` instead of `/` (a routing-target change only — `signIn()`/`signUp()`/`AuthContext`/`ProtectedRoute` themselves are untouched); a sign-in reached via a protected-route redirect still returns the user to whatever page they originally requested, unchanged.

## 4. Dashboard Information Architecture

Implemented in the brief's own intended order: Greeting/context (`PageHeader`, with a real "+ New Analysis" CTA) → KPI cards → Procurement Group Overview + Latest Decision (side by side) → Savings Analytics + Recent Analyses (side by side) → Action panel.

## 5. App Shell

Reused `Sidebar`/`TopBar`/`AppLayout` entirely. `Sidebar.jsx`'s nav items changed to exactly this phase's own suggested set — **Dashboard, New Analysis, Run History** — replacing "Home" (which pointed at "/", now the public page, not part of the authenticated app) and dropping the standalone "Results" link (it was never a real destination — `/results` only ever has content via router state handed off from `/analyze` or `/history`, unchanged since Phase 7D/7F; it remains a fully working route, just no longer a top-level nav entry). "Insights"/"Settings" were **omitted**, not shown as disabled/fake links — neither page exists, and this phase's own instruction explicitly forbids "dead links that look functional." `TopBar.jsx` gained one new `ROUTE_TITLES` entry (`/dashboard`); its authenticated-user email display and Sign Out button are completely unchanged.

## 6. KPI Metrics

All four reuse the existing `MetricCard` component (`results/MetricCard.jsx`, extended in UI-1 with an optional `tone`, now also an optional `hint`).

| Metric | Source | Calculation | Empty state |
|---|---|---|---|
| Total Analyses | `GET /procurement/runs` length | `summaries.length` — the true, uncapped total, always accurate regardless of the detail-fetch cap (Section 21) | `0` shown plainly (a real, honest zero — the whole dashboard shows its own bigger empty state at this point, Section 14) |
| Total Expected Savings | `final_selection.total_savings_rs`, summed across fetched runs with a selection | Plain sum, exactly mirroring `SavingsSummary.jsx`'s own "never re-sum, read the backend's own total" principle, just across multiple runs | `—` with hint "Available after a group is selected" (never a misleading `₹0.00`) |
| Vendors Evaluated | `result.total_vendors_submitted`, summed | Plain sum | `0` (a real vendor count of zero submitted vendors so far) |
| Collaborative Groups | `result.selected_group_count`, summed | Plain sum | `0` |

## 7. Latest Decision

`LatestDecisionCard.jsx` finds the most recent fetched run with an actual selected group (`getLatestSelectedRun` in `dashboardMetrics.js`) and reuses the **existing, unmodified** `DecisionStateBadge`, reading its state from the real `final_decision_state` field (never assumed to be `BUY_TOGETHER`, even though that is the only value a selected group can structurally have). "View Decision →" passes `state={{ result: ... }}` on the `Link` — the exact same router-state hand-off `AnalysisForm.jsx`/`HistoryPage.jsx` already use to reach `ResultsPage.jsx`. If no run has a selection yet, a polished `EmptyState` with a "Start an Analysis" CTA is shown instead — never a fabricated decision.

## 8. Procurement Network Visualization

Named **"Procurement Group Overview"**, deliberately not "Network" or "Map" — the result payload exposes group **membership** (`vendor_ids`) but no geographic coordinates or distances, so an inline SVG hub-and-members diagram is built from the real `vendor_ids` of the latest selected group, with a caption stating plainly it is not a geographic map. No map/graph library was added — this reuses UI-2's `HeroNetwork` inline-SVG technique, but every label is a real vendor ID this time (confirmed against the real persisted run: `BOWENPALLY_POTATO_01`, `ERRAGADDA_POTATO_01`, `GUDIMALKAPUR_POTATO_01`, `MEHDIPATNAM_POTATO_01` — Section 24). Clicking or keyboard-activating (`Enter`/`Space`) a node shows its real vendor ID below the diagram — no complex graph physics, no 3D, no invented geographic relationship. With no selected group yet, a clearly-labeled empty state is shown instead.

## 9. Savings Analytics

`dashboardMetrics.js`'s `buildSavingsSeries()` (oldest-first, real runs with a selection only). Zero data points → an empty state. Exactly one → a single large figure (no trend manufactured from one point, per this phase's own explicit instruction — directly matches the real current state, Section 24). Two or more → a small inline SVG bar chart (no chart library added), each bar's height driven by the real savings value for that run.

## 10. Recent Analyses

`RecentAnalyses.jsx` — deliberately **not** a reuse of `history/RunHistoryTable.jsx` (left completely unchanged; `HistoryPage`'s own lightweight-summary-then-fetch-on-click flow is untouched). This list can show real vendor/savings figures directly per row because the dashboard already fetched full detail for these runs (Section 21) — no extra request per row. Reuses `historyHelpers.js`, `runStatusMeta.js`, `resultHelpers.js`, and `Badge`/`Card`/`Button`/`EmptyState` — no duplicate formatting logic. Only a "View Analysis" action exists (routes to `/results` with real router state) — no delete/edit/duplicate, per this phase's own "do not invent CRUD" instruction.

## 11. Action Panel

`ActionPanel.jsx` — one legitimate CTA ("Start New Analysis" → `/analyze`), no fabricated alert or recommendation.

## 12. Loading States

`DashboardSkeleton.jsx` — shaped placeholder blocks (KPI row + two 2-panel rows) with a subtle CSS shimmer, shown by `DashboardPage.jsx` while `useDashboardData`'s `status` is `"loading"`. No real number is ever shown prematurely; the shimmer respects `prefers-reduced-motion` via the existing global rule with no extra code.

## 13. Error States

Reuses the existing `ErrorState` component with a "Try Again" button wired to the hook's `reload()`. The hook's own error messages are friendly (`describeError` in `useDashboardData.js`, mirroring `historyHelpers.js`'s existing convention) — no stack trace, no SQL error, no JWT/Supabase internal, no connection string is ever exposed to this layer or beyond it.

## 14. Real Data Handling

No fake procurement runs, no fake statistics, no fake "AI" labeling anywhere (`decision engine`/`optimization`/`explainable decision` language only, matching the project's established, honest positioning). Every number on this page is either directly read from a real API response or a plain, documented sum/count over real values (`dashboardMetrics.js`, Sections 6–9) — confirmed correct against the actual live persisted run in Section 24.

## 15. Ownership / Authentication Preservation

**Not modified**: `backend/`, `supabase/`, `frontend/src/auth/{AuthContext.jsx, useAuth.js, ProtectedRoute.jsx, authContextObject.js}`, `frontend/src/lib/supabase.js`, `frontend/src/api/{client.js, procurementApi.js}`. No `user_id` field, query parameter, or form field was added anywhere in the frontend — `useDashboardData.js` calls only the existing `getProcurementRuns()`/`getProcurementRun(runId)` functions, exactly as `HistoryPage.jsx` already does, relying entirely on the backend's own existing ownership enforcement (Phase 8F/8G, unchanged) for data isolation. `/dashboard` is protected by the identical `ProtectedRoute` mechanism as every other protected route — confirmed live (Section 23): an unauthenticated visit redirects to `/signin` at every viewport.

## 16. Responsive Design

`dashboard.css`'s two-panel grids (`Network Overview + Latest Decision`, `Savings Analytics + Recent Analyses`) collapse to a single column below 960px; the KPI row reuses UI-2's existing responsive `.value-grid`. Verified live (desktop/tablet/mobile) for every page reachable without real credentials — no horizontal overflow anywhere (Section 23).

## 17. Accessibility

Semantic structure throughout (`PageHeader`'s existing `<h1>`, `<section>`/`<ul>`/`<li>` in `RecentAnalyses`). The Procurement Group Overview SVG has a real `aria-label` naming every vendor ID it contains (an accessible text equivalent, not a decorative image); each vendor node is a real, keyboard-reachable, `role="button"` element with `aria-pressed` state and `Enter`/`Space` handling, and the selected-vendor readout below the diagram is `aria-live="polite"`. The loading skeleton is `role="status"` with a descriptive `aria-label`. Every decision state still carries real label text via the unmodified `DecisionStateBadge` — never color alone.

## 18. Animation / Motion

One deliberate entrance (`.animate-in` on the dashboard's intro header, reusing UI-1/UI-2's existing utility) plus the existing global hover/focus transitions on cards and buttons. The loading skeleton's shimmer is the only other animation, and — like everywhere else in this project — the existing global `prefers-reduced-motion` rule neutralizes all of it automatically, with zero dashboard-specific code required.

## 19. Components Reused

`MetricCard`, `Card` (including its `elevated`/`highlighted` variants from UI-1), `Button`, `Badge`, `DecisionStateBadge`, `EmptyState`, `ErrorState`, `PageHeader`, and the existing `historyHelpers.js`/`resultHelpers.js`/`runStatusMeta.js` formatting helpers — all completely unmodified except `MetricCard`'s new optional `hint` prop (Section 6).

## 20. Components Created

`pages/DashboardPage.jsx`; `components/dashboard/{useDashboardData.js, dashboardMetrics.js, KPISection.jsx, LatestDecisionCard.jsx, NetworkOverview.jsx, SavingsAnalytics.jsx, RecentAnalyses.jsx, ActionPanel.jsx, DashboardSkeleton.jsx}`; `styles/dashboard.css`.

## 21. Files Changed

**Created:** `frontend/src/pages/DashboardPage.jsx`, `frontend/src/components/dashboard/useDashboardData.js`, `frontend/src/components/dashboard/dashboardMetrics.js`, `frontend/src/components/dashboard/KPISection.jsx`, `frontend/src/components/dashboard/LatestDecisionCard.jsx`, `frontend/src/components/dashboard/NetworkOverview.jsx`, `frontend/src/components/dashboard/SavingsAnalytics.jsx`, `frontend/src/components/dashboard/RecentAnalyses.jsx`, `frontend/src/components/dashboard/ActionPanel.jsx`, `frontend/src/components/dashboard/DashboardSkeleton.jsx`, `frontend/src/styles/dashboard.css`, `reports/ui3_premium_procurement_dashboard.md` (this file).

**Modified:** `frontend/src/routes/AppRoutes.jsx` (added `/dashboard`), `frontend/src/components/layout/Sidebar.jsx` (nav items, Section 5), `frontend/src/components/layout/TopBar.jsx` (one `ROUTE_TITLES` entry), `frontend/src/main.jsx` (added `import './styles/dashboard.css'`), `frontend/src/pages/SignInPage.jsx` / `SignUpPage.jsx` (default post-auth redirect target, Section 3), `frontend/src/components/results/MetricCard.jsx` (optional `hint` prop), `frontend/src/styles/results.css` (`.metric-card-hint`).

**Not touched:** `backend/`, `supabase/` (confirmed via `git status`, identical to every prior baseline), `AnalysisPage.jsx`/`AnalysisForm.jsx`, `ResultsPage.jsx` and its own components, `HistoryPage.jsx`/`RunHistoryTable.jsx`, `AppLayout.jsx`, every UI-2 landing component, `frontend/src/auth/*`, `frontend/src/api/*`.

## 22. Verification

```
python -m pytest -q     →  178 passed, 0 failed, 0 skipped   (unchanged baseline)
npm run build             →  succeeds (150 modules -- up from 139, since the new
                              dashboard components are now imported/bundled)
npm run lint               →  clean, 0 warnings, 0 errors -- including one legitimate
                              warning found and fixed (react/set-state-in-effect in
                              useDashboardData.js: restructured so the mount-triggered
                              effect never calls setState synchronously at its own
                              top level, only inside its async .then()/.catch(); the
                              retry button's onClick is what now resets to "loading",
                              per the lint rule's own suggested fix)
```

## 23. Browser Verification

Real Playwright (Chromium), the same isolated scratchpad install used in UI-1/UI-2 — **24 checks across desktop (1440×900), tablet (820×1180), and mobile (375×812), all PASS**, covering everything genuinely testable without real Supabase credentials:
- Unauthenticated `/dashboard` redirects to `/signin` at every viewport (the real `ProtectedRoute`, unmocked).
- The public landing page (`/`) remains intact, no overflow.
- Unauthenticated `/analyze` and `/history` still redirect correctly (no regression).
- The sidebar (visible on `/signin`, inside the unchanged `AppLayout`) shows exactly `Dashboard, New Analysis, Run History`.
- Zero console/page errors throughout.

**Not covered by this section**: the dashboard's own populated/loading/error rendering, since reaching `/dashboard` requires a real authenticated session this environment has no credentials for — see Section 24 for how that gap was handled honestly.

## 24. Live Data Verification

The one real persisted run (`commodity: POTATO_HYD_2026_09`, `run_status: COMPLETED`) was read **directly and read-only** from the live database (the same safe technique used in Phase 8F/8G's audits — no write, no mutation, no credential printed) to obtain its exact real API-response JSON. `dashboardMetrics.js`'s actual aggregation logic was then run, unmodified, against that real payload (as a plain Node script, not inside the browser):

```
totalAnalyses: 1
totalSavings: 3732.6000000000004        →  formats to ₹3,732.60, matching exactly
totalVendorsEvaluated: 4                 →  matches exactly
totalSelectedGroups: 1                   →  matches exactly
decisionCounts: { BUY_TOGETHER: 11 }     →  all 11 evaluated candidate groups were BUY_TOGETHER
latest selected group vendor_ids: [BOWENPALLY_POTATO_01, ERRAGADDA_POTATO_01,
                                    GUDIMALKAPUR_POTATO_01, MEHDIPATNAM_POTATO_01]
latest selected group decision state: BUY_TOGETHER
```

Every one of these values exactly matches the real numbers reported at the start of this phase's own instructions (4 vendors, 1 selected group, BUY TOGETHER, ₹3,732.60) — confirming the dashboard's calculation logic is genuinely correct against real, live, persisted data, not merely "looks right" from code inspection alone.

**What this does NOT cover, stated honestly**: an actual real-browser session, signed in with real Supabase credentials, watching `/dashboard` paint this data on screen. This environment has no login password and, consistent with every prior phase in this project, did not request one or fabricate a session. **This is the one remaining verification step, and it requires the project owner** — sign in and open `/dashboard`; the KPI cards, Latest Decision card, and Procurement Group Overview should show exactly the figures and vendor IDs above.

## 25. Regression Checks

- `python -m pytest -q` — 178 passed, identical to the pre-UI-3 baseline; no backend file touched.
- `/`, `/analyze`, `/history`, `/signin` — all verified live, unaffected (Section 23).
- `/results` — still a fully working route (reachable via router state from `/analyze`, `/history`, or now the dashboard); its own page/components were not modified.
- Sign-out — `TopBar.jsx`'s `handleSignOut` is completely unchanged (still navigates to `/` after signing out, correctly distinct from the new default sign-**in** target of `/dashboard`).

## 26. Known Limitations

A full real-browser, real-credential walkthrough of the populated dashboard was not performed (Section 24) — the calculation logic was verified against the real persisted data directly, but the final on-screen rendering step needs the project owner. The dashboard was only verifiable against **one** real run in this project's actual current state; the "2+ runs" bar-chart and "10+ runs, capped at 20" code paths (Sections 9, 21) were verified by code review and the unit-level metrics computation, not against genuine multi-run live data, since fabricating additional real runs was correctly out of scope. `/results` and `/history` retain their own pre-UI-3 visual design, as instructed (not redesigned this phase).

## 27. Final Verdict

**PASS WITH DOCUMENTED LIMITATIONS**
