# UI-7 — Procurement Insights & Analytics

**Date:** 2026-09-16

## 1. Objective

Implement a premium `/insights` experience that helps a user understand patterns across their own real procurement runs — decision distribution, expected savings, commodity/vendor/group-size patterns — where **data truth is more important than visual impact**: any insight the available data cannot honestly support is replaced by an explicit "not enough historical data" state rather than a fabricated chart or claim.

## 2. Existing Data Sources Inspected

Read in full before writing anything: `components/dashboard/{useDashboardData.js, dashboardMetrics.js, RecentAnalyses.jsx, SavingsAnalytics.jsx}` (UI-3), `components/history/{useHistoryData.js, historyFilters.js, historyHelpers.js}` (UI-6), `components/results/resultHelpers.js`/`runStatusMeta.js` (UI-5), `api/procurementApi.js`, `api/client.js`, `routes/AppRoutes.jsx`, and `components/layout/{Sidebar.jsx, TopBar.jsx}` (to find the exact spot UI-6's own comment had already flagged: "Insights"/"Settings" were previously *considered and deliberately omitted*, not left as dead links).

## 3. Actual API Fields Available

Nothing new was inspected here beyond what UI-6 already established and documented (`reports/ui6_premium_run_history.md` Section 3) — re-confirmed, not re-derived:
- `GET /procurement/runs` returns every run (`run_id, created_at, commodity, run_status`), unbounded, no pagination.
- `GET /procurement/runs/{run_id}` returns the full `{run_id, created_at, commodity, run_status, input, result}` — the same shape History already fetches.
- The real, live database currently contains exactly **1** run (`POTATO_HYD_2026_09`, `COMPLETED`) — re-verified via the same read-only query used in the UI-6 report.

## 4. Data Availability Limitations

| Metric | Available? | Source | Derivation | Safe to display? |
|---|---|---|---|---|
| Total run count | Yes, always | `GET /procurement/runs` length | None (direct) | Yes, unconditionally |
| Commodity per run | Yes, always | list response | None (direct) | Yes, unconditionally |
| Per-run decision state | Only for a run whose detail was fetched | `detail.result.final_selection.selected_results[0].final_decision_state` | `getPrimaryDecisionState()` (UI-5/6, reused) | Yes, for enriched runs only |
| Expected savings per run | Only for an enriched run with a selection | `detail.result.final_selection.total_savings_rs` | None (direct) | Yes, for enriched+selected runs only |
| Vendor IDs per run | Only for an enriched run | `detail.input.vendor_submissions[].vendor_id` | None (direct) | Yes, for enriched runs only |
| Selected-group size | Only for an enriched run with a selection | `detail.result.final_selection.selected_results[].vendor_ids.length` | None (direct) | Yes, for enriched+selected runs only |
| "Which vendor is most reliable" | **No** | — | No defined reliability metric exists anywhere in the backend | **No — never implemented** |
| "Is procurement improving over time" | **No** | — | No defined improvement/quality metric exists | **No — never implemented** |
| A true lifetime trend across *all* runs | **No, bounded** | list is unbounded but detail-enrichment is capped | `useHistoryData.js`'s `HISTORY_DETAIL_FETCH_LIMIT` (30) | Only for the enriched subset, stated honestly |

Because the backend has **no pagination** and detail-enrichment is necessarily bounded (Section 19 below), every decision/savings/vendor/group-size insight is scoped to the most recent `HISTORY_DETAIL_FETCH_LIMIT` (30) runs — the Analytics Scope banner (Section 5) states this explicitly whenever it applies.

## 5. Analytics Implemented

- **Run Activity** — Total Runs (always the true, unbounded count).
- **Decision Distribution** — real per-run primary-decision counts (`BUY_TOGETHER`/`WAIT_OR_EXPAND_GROUP`/`DO_NOT_BUY_TOGETHER`/`ABSTAIN`/"No group selected"), shown as a labeled proportional bar with real percentages, or an honest single-fact/limited-data state below the threshold.
- **Savings Overview** — Total/Average/Highest **expected** savings across analyzed runs (2+ data points), or a single labeled value with "1 analyzed run" context, or "not enough historical data" with zero.
- **Savings By Run** — reuses UI-3's existing `SavingsAnalytics.jsx` component directly (its own established 0/1/2+ graduated behavior), fed with `dashboardMetrics.js`'s existing `buildSavingsSeries()`.
- **Commodity Analysis** — runs and expected savings by commodity, sorted by run count only (never "best").
- **Vendor Participation** — a real table (vendor ID, runs observed, selected-group appearances), scoped explicitly to runs with fetched detail.
- **Collaboration Group Size** — real distribution of selected-group sizes.
- **Evidence-Based Observations** — a list of plain sentences, each a direct restatement of one of the counts above (see Section 7 for the exact rule and a real bug found/fixed in this logic).
- **What These Analytics Mean** — a concise, static methodology note (expected ≠ realized, no AI involved, historical only).

## 6. Analytics Intentionally NOT Implemented, and Why

- **Vendor "reliability"/"best vendor" ranking** — no metric for this exists anywhere in the backend (no fulfillment tracking, no repeat-purchase data); implementing one would be pure invention. Only "most frequently observed" (a plain, defensible frequency count) is used, and only when genuinely unique (Section 7).
- **"Procurement is improving" / trend commentary** — the backend defines no quality/improvement metric across runs; only real per-run counts are shown, with the reader left to interpret them.
- **A true full-history trend** — the backend's `GET /procurement/runs` has no pagination, and fetching detail for every historical run without bound would be an unreasonable request load (Rule 20). Insights therefore analyzes the same bounded, most-recent subset History already established, stated honestly (Section 4/19) rather than silently presented as complete.
- **Confidence scores / AI recommendations** — no such backend component exists; adding one would violate Rule 23 outright.
- **A backend aggregation/statistics endpoint** — explicitly forbidden (Rule 1/28); everything here is presentation-layer aggregation over data the existing endpoints already return.

## 7. Aggregation Logic

All new aggregation lives in one pure, dependency-free module, `components/insights/insightsMetrics.js`: `buildDecisionDistribution`, `summarizeSavings`, `buildCommodityBreakdown`, `buildVendorParticipation`, `buildGroupSizeDistribution`, `buildEvidenceObservations`. Reused rather than duplicated: `getEntryDecisionFilterValue`/`DECISION_FILTER_OPTIONS` (`history/historyFilters.js`, UI-6) for per-run decision classification, and `buildSavingsSeries` (`dashboard/dashboardMetrics.js`, UI-3) for the savings-over-time series.

**A distinct metric from Dashboard's own `decisionCounts`:** UI-3's `buildDashboardMetrics()` already computes a "decision" count, but it counts *every individual candidate group's* decision across all evaluated groups in all fetched runs — a different question ("how did each candidate group evaluate") from Insights' own Decision Distribution, which counts *one primary classification per run* ("how did each run's own outcome turn out" — matching this phase's own brief example, "BUY TOGETHER — 6 of 10 runs"). Both are real, valid, already-existing metrics; they are never conflated.

**A real bug found and fixed during verification:** the first implementation of `buildEvidenceObservations()`'s "most frequently observed vendor" and "most common selected group size" statements picked the top-sorted entry even when it was **tied** with another value — in one verification fixture, two vendors were genuinely tied at 1 appearance each, and the code was about to assert one of them was "the most frequently observed" purely because of JavaScript's incidental object-key ordering (integer-like keys sort numerically ascending regardless of insertion order), not because the data actually supported a unique winner. This is exactly the class of overclaiming Rule 3/10 forbids. **Fixed:** each superlative observation is now only produced when the top count strictly exceeds the second-highest one; a genuine tie is a real result the data does not resolve, so the observation is omitted rather than guessed. Verified with two dedicated harness scenarios — one deliberately tied (confirms omission), one with a genuine unique winner (confirms the positive claim still appears) — see Section 15.

A second, smaller inconsistency was caught and fixed during visual review: Vendor Participation was originally gated behind the same "2+ runs" threshold as the Decision/Group-Size bar charts, but a vendor table (like Commodity Breakdown) is a plain factual listing, not a proportional-distribution visual that could overstate a single data point — so it is now shown starting at 1 considered run, while the separate "most frequently observed vendor" *superlative claim* remains correctly gated (and additionally requires a unique winner, per the fix above).

## 8. Components Created

`frontend/src/components/insights/{insightsMetrics.js, LimitedDataState.jsx, DataScopeBanner.jsx, InsightsOverviewMetrics.jsx, DecisionDistribution.jsx, SavingsOverview.jsx, CommodityBreakdown.jsx, VendorParticipation.jsx, GroupSizeAnalysis.jsx, EvidenceObservations.jsx, MethodologyNote.jsx, InsightsSkeleton.jsx}`, `frontend/src/pages/InsightsPage.jsx`, `frontend/src/styles/insights.css`.

## 9. Components Modified

`routes/AppRoutes.jsx` (added the `/insights` route, protected by the same unmodified `ProtectedRoute`, inside the same `AppLayout`), `components/layout/Sidebar.jsx` (added the "Insights" nav item — UI-6's own comment had already flagged this as a deliberately-omitted-until-real item), `components/layout/TopBar.jsx` (added the `/insights` route title), `components/dashboard/ActionPanel.jsx` (added one more legitimate link, "View Insights →", alongside its existing CTA — completing the coherent flow without redesigning the panel), `styles/dashboard.css` (one small additive rule for that link's layout), `main.jsx` (one new CSS import). `components/results/resultHelpers.js` was **not** modified this phase (its `getPrimaryDecisionState` export, added in UI-6, was reused as-is).

## 10. Route/Navigation Changes

`/insights` is a genuinely new, working, protected route (not a placeholder) reached from: the sidebar nav ("Insights", positioned right after "Dashboard"), the Dashboard's `ActionPanel` ("View Insights →"), and the Insights page's own header actions ("Run History" / "New Analysis"), completing the brief's own "Dashboard → Insights → History → Results" flow. No other page's navigation shell was duplicated or redesigned.

## 11. Responsive Behavior

Verified at 1440px/1024px/390px (Section 15). The overview metrics grid, decision-distribution/group-size proportional bars, and commodity/vendor tables all reuse the exact same responsive rules already established in `results.css`/`history.css`/`dashboard.css` (`.metrics-grid`, `.vendor-economics-bar-*`, `.history-table-wrapper`) — no new responsive breakpoints were needed beyond `insights.css`'s own small `LimitedDataState` padding adjustment below 480px. Every table keeps its existing horizontal-scroll wrapper rather than ever causing page-level overflow.

## 12. Accessibility

Semantic `<h2 id="...">`/`aria-labelledby` pairing on every section; both proportional-bar visualizations (Decision Distribution, Group Size) carry a real `role="img"` with a complete textual `aria-label` summarizing every segment in words (e.g. "Buy Together: 2 of 3 runs, No group selected: 1 of 3 runs"), with the decorative bar markup itself `aria-hidden` to avoid double-announcement; decision meaning is never conveyed by color alone (reusing `DecisionStateBadge`/`Badge` labels, unchanged); every table uses real `<th scope="col">` headers; `LimitedDataState` uses `role="status"`.

## 13. Reduced-Motion Behavior

No new animation or shimmer implementation was added — `InsightsSkeleton.jsx` reuses UI-3's existing `.skeleton-block` shimmer (`styles/dashboard.css`), and the proportional-bar fill reuses UI-5's existing `.vendor-economics-bar-fill` transition — both already governed by the single, site-wide `prefers-reduced-motion` rule in `global.css` established in UI-1, with zero page-specific code required.

## 14. Real-Data Verification

The real, previously-persisted `POTATO_HYD_2026_09` run (4 vendors, `BUY_TOGETHER`, ₹3,732.60 — the same run UI-5/UI-6's own reports already verified) was rendered by the actual, unmodified `InsightsPage`/`insightsMetrics.js` code via the harness described in Section 15. In the single-run scenario (matching the **real, current state of the live database**, re-confirmed in Section 3), Insights correctly: showed Total Runs = 1, Expected Savings = ₹3,732.60, Buy Together Decisions = 1 of 1; showed Decision Distribution as an honest "Limited data... classified as Buy Together" statement rather than a chart; showed Savings Overview as a single labeled value rather than a fabricated Total/Average/Highest trio; showed the real 4-vendor Vendor Participation table; and correctly showed "Not enough historical data" for Group Size Analysis (only one selected group exists). None of these numbers are hardcoded anywhere in the new code — they flow from the fixture exactly as a real API response would.

## 15. Browser Verification

No real Supabase session was available, and none was fabricated. Two complementary techniques were used, matching UI-5/UI-6's own established, already-accepted pattern:

**A. Unauthenticated structural checks** against the real production `vite preview` build: `/insights`, `/history`, `/results`, `/analyze`, `/dashboard` all correctly redirect an unauthenticated visitor to `/signin`; `/` still loads. **6/6 passed.**

**B. Full real-and-synthetic-data rendering** — a temporary, self-contained harness (`harness.html` + `_harness_main.jsx` + `_harness_fixtures.js`, all under `frontend/`, never imported by `index.html`/`main.jsx`/any route, and **deleted before this report was written**, confirmed via `git status`) rendered the real, completely unmodified `InsightsPage.jsx` inside a `MemoryRouter` with `window.fetch` intercepted to serve canned responses, exactly as UI-6's own harness did. Five scenarios were exercised at 1440px/1024px/390px:
  - **`multi`** (4 runs: the real `POTATO_HYD_2026_09` plus 3 clearly-synthetic runs, engineered with a genuine non-tied top vendor/group-size): confirmed every section's real counts, percentages, sums, and the two positive "most frequent/common" observations.
  - **`tied`** (3 runs, deliberately tied vendor/group-size counts): confirmed the tie-guard fix (Section 7) correctly **omits** both superlative observations while still showing the real, non-superlative counts.
  - **`single`** (the real 1-run scenario, matching the live database exactly): confirmed every limited-data fallback renders correctly and no fake distribution/trend appears (Section 14).
  - **`empty`** / **`error`** / **`many`** (35 runs, only 3 of the first 30 detail-fetches actually resolve in the fixture): confirmed the empty state, the safe error message (raw exception text never reaches the page), and that the Analytics Scope banner honestly reports the *actual* enriched count (3) rather than the attempted cap (30).

**69/69 checks passed** — no console errors or horizontal overflow at any viewport across any scenario, keyboard focus reaches an interactive element, and every real number matched its expected, hand-computed value exactly.

**Not verified:** an actual authenticated click-through (sign in → Dashboard → Insights → History → Results) in the live deployed app — this requires a real Supabase session this environment does not have.

## 16. Build Result

`npm run build` — **186 modules transformed, 0 errors** (up from 172 after UI-6, reflecting the 14 new Insights files).

## 17. Lint Result

`npm run lint` (oxlint) — **0 warnings**.

## 18. Backend Test Result

`python -m pytest -q` — **178 passed, 0 failed, 0 skipped** (unchanged — confirms the backend was genuinely never touched).

## 19. Authentication Verification

Not possible in this environment — no real Supabase session was available, and none was fabricated. `ProtectedRoute`/`AuthContext` were not modified in any way; Section 15A's redirect checks confirm `/insights` is gated identically to every other protected route. The residual, unverified risk is narrow and identical in kind to every prior UI phase's own documented limitation.

## 20. Known Limitations

- **No backend pagination exists** (re-confirmed from UI-6, Section 3/4) — decision/savings/vendor/group-size insights are therefore bounded to the same `HISTORY_DETAIL_FETCH_LIMIT` (30) most-recent runs History already established; the Analytics Scope banner states this honestly whenever the true total exceeds what was actually enriched.
- **A genuine tie never produces a "most frequent/common" claim** (Section 7) — this is a deliberate correctness choice, not a bug, but it does mean that in a tied dataset, Evidence-Based Observations will show fewer statements than a less careful implementation might have shown.
- With only 1 real analyzed run currently in the live database, most distribution/trend/group-size sections correctly render their "limited data" states rather than a chart — this is the intended, honest behavior for the system's actual current data volume, not a defect (Section 14).
- No authenticated end-to-end verification was possible (Section 19).

## 21. Backend Confirmation

**Backend NOT modified. Procurement engine NOT modified. Authentication/RLS/JWT NOT modified. No new backend endpoint, database column, table, or migration.** Confirmed by `git status`: zero changes under `backend/` or `supabase/` beyond what was already present from prior phases before this session began. `python -m pytest -q` remains 178 passed / 0 failed / 0 skipped.

---

## UI-7 IMPLEMENTATION SUMMARY

**What changed:** A new `/insights` page — Analytics Scope → Overview Metrics → Decision Distribution → Savings Overview → Savings By Run → Commodity Analysis → Vendor Participation → Collaboration Group Size → Evidence-Based Observations → What These Analytics Mean — reachable from the sidebar, the Dashboard action panel, and the page's own header actions.

**Data sources inspected:** `useDashboardData.js`/`dashboardMetrics.js` (UI-3), `useHistoryData.js`/`historyFilters.js` (UI-6), `resultHelpers.js`/`runStatusMeta.js` (UI-5), `api/procurementApi.js`/`api/client.js`, `routes/AppRoutes.jsx`, `Sidebar.jsx`/`TopBar.jsx`, and the real, live `procurement_runs` table (re-confirmed: 1 real row).

**Analytics implemented:** Total runs; per-run decision distribution; expected-savings total/average/highest; expected savings by run (reusing UI-3's `SavingsAnalytics`); commodity breakdown; vendor participation; selected-group-size distribution; evidence-based observations; a static methodology note.

**Analytics intentionally omitted:** vendor "reliability"/ranking, "procurement is improving" commentary, a true unbounded-history trend, any AI confidence/recommendation, any backend-aggregated statistic — none is supported by real data or permitted backend scope (Section 6).

**Files created:** `components/insights/{insightsMetrics.js, LimitedDataState.jsx, DataScopeBanner.jsx, InsightsOverviewMetrics.jsx, DecisionDistribution.jsx, SavingsOverview.jsx, CommodityBreakdown.jsx, VendorParticipation.jsx, GroupSizeAnalysis.jsx, EvidenceObservations.jsx, MethodologyNote.jsx, InsightsSkeleton.jsx}`, `pages/InsightsPage.jsx`, `styles/insights.css`.

**Files modified:** `routes/AppRoutes.jsx`, `components/layout/Sidebar.jsx`, `components/layout/TopBar.jsx`, `components/dashboard/ActionPanel.jsx`, `styles/dashboard.css`, `main.jsx`.

**Files deleted:** none.

**Backend changed:** NO
**Procurement engine changed:** NO
**Authentication/security changed:** NO

**Backend tests:** 178 passed, 0 failed, 0 skipped.
**Build:** clean, 186 modules, 0 errors.
**Lint:** clean, 0 warnings.
**Browser verification:** 6/6 unauthenticated redirect checks + 69/69 checks from a real-Chromium harness across 5 scenarios (multi-run with a genuine winner, tied-data omission, the real single-run state, empty, error, and a 35-run cap-boundary case) at 1440px/1024px/390px.
**Real-data verification:** the real `POTATO_HYD_2026_09` run rendered correctly in the single-run scenario matching the live database's actual current state — 1 run, ₹3,732.60 expected savings, Buy Together — with every distribution/trend/group-size section correctly showing an honest limited-data state instead of a fabricated chart.
**Authenticated verification:** not possible — no real Supabase session available; documented rather than fabricated.
**Limitations:** insights are bounded to the same 30-most-recent-run enrichment cap History already established (no backend pagination exists); with only 1 real run currently persisted, most distribution sections correctly show "limited data" today.

**Report:** `reports/ui7_procurement_insights.md`

**Git operations:** NONE
