# UI-5 — Premium Procurement Results Dashboard

**Date:** 2026-09-16

## 1. Objective

Redesign `/results` (and only `/results`) into a premium "Procurement Decision Cockpit": a page whose visual hierarchy makes the decision itself the first thing a reader sees, followed by the economics behind it, the vendors involved, the alternatives considered, and any warnings — with every displayed value read directly from the backend's response and nothing fabricated.

## 2. Files Inspected

Before writing any code: the full existing results implementation (`pages/ResultsPage.jsx`, `components/results/{ResultsSummary,FinalSelectionSection,SavingsSummary,VendorOutcomesTable,GroupDecisionList,GroupFormationSummary,DecisionExplanation,resultHelpers,runStatusMeta,MetricCard}.jsx/js`), how History reopens a run (`pages/HistoryPage.jsx`, confirming its `getProcurementRun`/`navigate("/results", {state})` hand-off), the API client (`api/procurementApi.js`), and the full backend contract chain read directly from source: `backend/models/run_contracts.py` (`ProcurementRunResult`, `RunStatus`), `backend/models/decision_contracts.py` (`EvaluatedGroupResult`, `FinalSelectionResult`), `backend/models/group_formation_contracts.py` (`CandidateGroupRecord`, `GroupFormationResult`, `PoolDiagnostic`), `backend/models/contracts.py` (`GroupDecisionResult`, `PerVendorAllocation`, `VendorInput`), `backend/models/batch_contracts.py` (`VendorEligibilityResult`, `BatchEligibilityResult`, `ContextValidationResult`), `backend/models/enums.py` (`DecisionState`, `OutcomeKind`), `backend/models/reasons.py` (`ContextValidationReason`), `backend/api/routes/procurement.py` (all three route handlers, to confirm exactly what each endpoint returns), and `backend/services/selection.py` (to confirm exactly how `selected_results`/`non_selected_buy_together_results`/`wait_or_expand_results`/`do_not_buy_results`/`abstained_results` are partitioned — by **final**, post-refinement `decision_state`, not the base one). Also inspected the existing design system (`styles/variables.css`, `components.css`, `dashboard.css`, `landing.css`) and UI-3's `NetworkOverview.jsx` for its already-established hub-and-members SVG technique, reused rather than reinvented.

## 3. Actual Result API Contract Discovered

**Confirmed, not assumed:**
- `POST /procurement/analyze` returns the raw `ProcurementRunResult` only — **no `run_id` is ever returned to the caller**, even though the backend does persist one. A freshly-completed analysis genuinely has no run identifier available to the frontend; this is a real, pre-existing backend characteristic, not something this phase changed or worked around.
- `GET /procurement/runs/{run_id}` returns `{run_id, created_at, commodity, run_status, input, result}` — `run_id`/`created_at` **are** available here, but `HistoryPage.jsx` was previously discarding them before navigating to `/results` (passing only `stored.result`).
- The four `DecisionState` values are exactly `BUY_TOGETHER` / `WAIT_OR_EXPAND_GROUP` / `DO_NOT_BUY_TOGETHER` / `ABSTAIN` — no `NO_FEASIBLE_GROUP` or `EXPAND` state exists at the group level; a "no feasible group" situation is instead expressed via the six `RunStatus` values (`COMPLETED`, `COMPLETED_WITH_ABSTENTIONS`, `COMPLETED_NO_SELECTION`, `COMPLETED_NO_GROUPS`, `COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS`, `COMPLETED_INVALID_CONTEXT`) — a **run-level** concept the backend's own docstring explicitly warns must never be merged with the **group-level** `DecisionState`.
- `selection.py`'s `select_final_groups()` partitions candidates into `wait_or_expand_results`/`do_not_buy_results`/`abstained_results`/`non_selected_buy_together_results` by each candidate's own **final** (post-WAIT/EXPAND-refinement) decision state — confirmed by reading the function directly, not assumed from naming.

### Field map

| API field | Meaning | UI section |
|---|---|---|
| `run_status` | Run-level outcome (`RunStatus`) | Decision Hero (fallback headline when no group selected), hero note badge, Decision Summary |
| `commodity_id`, `context_date` | Run identity | Page header |
| `total_vendors_submitted`, `eligible_vendor_count`, `abstained_vendor_count`, `validation_error_vendor_count`, `candidate_group_count`, `selected_group_count` | Plain backend-computed counts | Key Decision Metrics, Decision Hero chips |
| `batch_eligibility.context_validation.{is_valid,reasons}` | Structural validity of the submitted context | Diagnostics |
| `batch_eligibility.{eligible,abstained,validation_error}_vendors[]` | Per-vendor outcome + `reason_detail` | Vendor Submission Detail (existing `VendorOutcomesTable`, unchanged); counts also surfaced in Diagnostics |
| `group_formation.pools`, `.singleton_vendor_ids`, `.diagnostics[].large_pool_warning` | Compatibility pools and non-blocking formation diagnostics | Candidate Groups Evaluated intro line; Diagnostics |
| `final_selection.selected_results[]` | The selected group(s): `decision` (full `GroupDecisionResult`), `final_decision_state`, `vendor_ids` | Decision Hero, Selected Procurement Group, Vendor Economics |
| `final_selection.total_savings_rs`, `.total_vendor_coverage`, `.tie_break_note` | Backend-computed totals (never re-summed) | Decision Hero, Key Decision Metrics, Decision Summary |
| `final_selection.all_evaluated_results[]` | Every evaluated candidate | Candidate Groups Evaluated |
| `final_selection.non_selected_buy_together_results`, `.wait_or_expand_results` | Overlap-excluded / still-pending groups | Diagnostics |
| `decision.{aggregate_quantity_kg,k_star,centroid_distance_km,within_d_max,moq_applicable,moq_met,individual_cost_total_rs,collaborative_cost_rs,savings_rs,per_vendor_allocation[]}` | Per-group economics | Selected Procurement Group facts, Vendor Economics bars/table, Candidate Group row detail |
| `per_vendor_allocation[].{vendor_id,share_rs,individual_savings_rs,consumption_time_days}` | Per-vendor cost share | Vendor Economics bars + `AllocationTable` |

## 4. UI Architecture

`ResultsPage.jsx` is now a thin orchestrator composing, in order: `DecisionHero` → `ResultMetricGrid` → `SelectedGroupCard` → `VendorEconomics` → `CandidateGroupsPanel` → `DecisionDiagnostics` → Vendor Submission Detail (collapsible, reuses unmodified `VendorOutcomesTable`) → `DecisionExplanation` (upgraded visual, same content) → `ResultSummary` → `ResultActions`. This directly follows the brief's 11-section hierarchy.

## 5. Components Created / Modified

**New** (`frontend/src/components/results/`): `DecisionHero.jsx`, `ResultMetricGrid.jsx`, `SelectedGroupCard.jsx`, `SelectedGroupNetwork.jsx`, `VendorEconomics.jsx`, `AllocationTable.jsx` (extracted, reused by both `VendorEconomics` and `CandidateGroupRow`), `CandidateGroupsPanel.jsx`, `CandidateGroupRow.jsx`, `DecisionDiagnostics.jsx`, `ResultSummary.jsx`, `ResultActions.jsx`.

**Modified:** `resultHelpers.js` (additive: `getSavingsPercent`, `formatPercent`, `getContextValidationReasonLabel`), `runStatusMeta.js` (additive: a `description` field per status, mirroring `decisionStateMeta.js`'s existing pattern), `DecisionExplanation.jsx` (same pipeline-stage text, restyled as a numbered timeline), `pages/ResultsPage.jsx` (fully restructured), `pages/HistoryPage.jsx` (one-line additive change: now forwards the real `run_id`/`created_at` it already has, previously discarded), `styles/results.css` (large new section; one dead rule set — `.explanation-steps`, superseded by `.decision-pipeline` — removed after confirming no other caller).

**Deleted** (fully superseded, single call site confirmed via grep before removal): `ResultsSummary.jsx` → `ResultMetricGrid.jsx`; `FinalSelectionSection.jsx` → split into `SelectedGroupCard.jsx` + `VendorEconomics.jsx`; `SavingsSummary.jsx` → folded into `DecisionHero.jsx`; `GroupDecisionList.jsx` → `CandidateGroupsPanel.jsx`/`CandidateGroupRow.jsx`; `GroupFormationSummary.jsx` → folded into `CandidateGroupsPanel.jsx`'s intro line.

**Reused unmodified:** `MetricCard.jsx`, `VendorOutcomesTable.jsx`, `Card`/`Button`/`Badge`/`EmptyState`/`ErrorState`/`PageHeader`, `DecisionStateBadge`/`decisionStateMeta.js`, and UI-3's `.network-overview-*` CSS classes (from `styles/dashboard.css`, already globally bundled via `main.jsx`) — the results-page network diagram reuses these exact classes rather than duplicating them.

## 6. Data Mapping

See the field-map table in Section 3. Two derived (not fabricated) values were added, both grounded in two already-backend-provided numbers: `getSavingsPercent(savings_rs, individual_cost_total_rs)` (a plain ratio, guarded against a missing/zero denominator, shown in Vendor Economics) and the Decision Hero's supporting sentence, which is built by interpolating real counts (`total_vendor_coverage`, `selected_results.length`, etc.) into a fixed template — never a number invented outside the response.

## 7. Result States Handled

- **Success (selection made):** Decision Hero headlines the real `final_decision_state` of the selected group (read from the response, never hardcoded as `"BUY_TOGETHER"`).
- **Success (no selection):** Decision Hero honestly falls back to the run's own `RunStatus` label + description (never merges a fabricated group-level decision with a run-level outcome, per the backend's own explicit warning) — verified with a structurally-valid synthetic fixture representing `COMPLETED_WITH_ABSTENTIONS` with zero selected groups (Section 12).
- **Malformed result:** `hasUsableResult()` check (unchanged logic) shows a safe `ErrorState` — never a raw exception/stack trace.
- **No result (fresh visit, refresh, or direct URL):** `EmptyState` with a "Start New Analysis" CTA — unchanged mechanism (this page performs no fetch of its own; see the note below).
- **Reopened from History:** now shows a real `Run #<id>` line and a "reopened from a run saved on …" note in the header when `runId`/`createdAt` are present in router state (HistoryPage.jsx's own additive change, Section 5) — omitted entirely for a freshly-completed analysis, where no such identifier exists (Section 3).
- **Partial/optional fields absent:** every new component reads through `??`/optional chaining exactly as the Phase 7E originals did (e.g., `final_selection?.selected_results ?? []`, `decision.per_vendor_allocation ?? []`) — no crash on a missing optional field, confirmed both by code inspection and by the synthetic edge-case fixture above.

**On "Loading" state:** `ResultsPage.jsx` performs **no fetch of its own** — it synchronously reads `location.state` on render, exactly as the Phase 7D/7E original did, per this phase's explicit "do not break existing routing" / "do not create a new backend endpoint" rules. There is therefore no asynchronous work for a loading skeleton to cover; adding one would only introduce an artificial delay with nothing behind it. This is a deliberate, honest scope decision, not an oversight — documented here rather than silently working around it.

## 8. Responsive Behavior

Tested at 1440px, 1024px, and 390px (plus visual review at each) via a real, no-credentials-needed rendering technique (Section 12). The metrics grid wraps from 6 → fewer columns; the Decision Hero, Selected Group, Vendor Economics, and Candidate Group cards all reflow to single-column stacking; the Vendor Economics totals row (`individual cost` / `collaborative cost` / `savings`) gets an explicit single-column rule below 480px after visual review showed it reading as cramped at `auto-fit` default; every table (`AllocationTable`, `VendorOutcomesTable`) keeps its own existing `overflow-x: auto` wrapper rather than ever causing page-level horizontal scroll. Automated `document.documentElement.scrollWidth <= clientWidth` checks passed at all three widths with zero violations.

## 9. Accessibility

Semantic `<h1>`/`<h2>` headings throughout (`aria-labelledby` pairs each section heading to its `<section>`); candidate group rows are real `<button>` elements with `aria-expanded`, keyboard-operable by default (no custom key handling needed); the network diagram's nodes remain keyboard-focusable with `Enter`/`Space` support (same technique as UI-3's `NetworkOverview.jsx`) and the SVG carries a real `aria-label` describing its content in words, not just visually; decision meaning is never conveyed by color alone — every `DecisionStateBadge`/`Badge` pairs its color with an explicit label and (for decision states) an icon; the Diagnostics list uses semantic `<ul>`/`<li>`; the Decision Summary uses a real `<dl>`.

## 10. Animation / Reduced-Motion

Only the pre-existing, global `.animate-in` entrance (via `PageHeader`) and the existing `--transition-slow`-based bar-fill transition (`.vendor-economics-bar-fill`, matching UI-3's `.savings-chart-bar` precedent) were used — no new animation library, no continuous/looping animation anywhere on this page. Both inherit the site-wide `prefers-reduced-motion` handling in `global.css` automatically, with zero page-specific code required (the same pattern every UI phase since UI-1 has relied on).

## 11. Verification Results

- `npm run build` — 163 modules transformed, 0 errors.
- `npm run lint` (oxlint) — 0 warnings.
- `python -m pytest -q` — **178 passed, 0 failed, 0 skipped** (unchanged from before this phase — confirms the backend was genuinely never touched).

## 12. Browser Test Results

No real Supabase session is available in this environment, and none was fabricated (per this phase's explicit instruction). Two complementary, genuinely real techniques were used instead:

**A. Unauthenticated structural checks** (real Playwright/Chromium against the production `vite preview` build): `/results`, `/analyze`, `/dashboard`, `/history` all correctly redirect an unauthenticated visitor to `/signin` (no `ProtectedRoute` regression), and `/` still loads. 5/5 passed.

**B. Full real-data rendering** (the most important verification for this phase, since the questions "does the decision cockpit actually work" cannot be answered by redirect checks alone): a temporary, self-contained test harness (`harness.html` + `_harness_main.jsx` + two fixture JSON files, all under `frontend/`, **never imported by `index.html`/`main.jsx`/any route, and deleted before this report was written** — confirmed via `git status`, which shows no such files) rendered the real, completely unmodified `ResultsPage.jsx` inside a `MemoryRouter`, with router state populated exactly the way `HistoryPage.jsx`/`AnalysisForm.jsx` already do. Two data sources were used:
  1. The **real, previously-persisted** `POTATO_HYD_2026_09` run (fetched read-only from the live database in an earlier phase; the same run UI-3's report already verified) — a genuine `BUY_TOGETHER` selection.
  2. A **structurally-valid synthetic fixture** (clearly a test-only construction, never presented as real data) representing a `COMPLETED_WITH_ABSTENTIONS` run with **zero** selected groups, to exercise the Decision Hero's honest fallback path and the empty/negative-savings candidate-row rendering.

Real Playwright automation against this harness, at 1440px/1024px/390px, with real Chromium (no mocking of React or the DOM): **29/29 checks passed** — no console errors at any viewport, no horizontal overflow at any viewport, the Decision Hero renders the real `Buy Together` state and real `₹3,732.60` savings figure, the metrics grid renders all 6 real values, the Selected Procurement Group shows the real 4 vendor IDs, the Candidate Groups panel renders all 11 real candidates (sorted, selected one auto-expanded and highlighted), the Diagnostics section correctly and honestly surfaces "10 other feasible group(s) were eligible but not selected" (derived from the real `non_selected_buy_together_results` array — 11 candidates − 1 selected = 10, confirmed arithmetically correct), the candidate-row expand/collapse interaction works, the reopened-from-History scenario correctly shows `Run #03dd9806`, and the no-result state renders the correct `EmptyState`. The synthetic no-selection fixture rendered with zero console errors, the Hero correctly falling back to the `COMPLETED_WITH_ABSTENTIONS` run-status headline (never fabricating a group decision), `Expected Savings` honestly showing "—" with a "Available after a group is selected" hint, and a `-₹50.00` negative savings figure formatting correctly for the one `DO_NOT_BUY_TOGETHER` candidate.

Screenshots were visually reviewed at all three widths; one real design issue was found and fixed as a result (the Vendor Economics totals row was cramped on narrow mobile — Section 8) before this report was written.

**Not verified:** an actual authenticated click-through in the live deployed app (sign in → run/reopen an analysis → view `/results`) — this requires a real Supabase session this environment does not have. Given the strength of technique B above (the real, unmodified page component, rendered by a real browser, against real backend data, via the same state-hand-off mechanism the real app uses), the residual risk this leaves is narrow: primarily whether `ProtectedRoute`/`AuthContext` (both completely untouched this phase) still correctly gate the route, which is separately confirmed by technique A.

## 13. Real-Data Verification

Confirmed via the harness (Section 12) against the real, previously-persisted `POTATO_HYD_2026_09` run:

| Expected (real, from the live database) | Rendered on the new page |
|---|---|
| 4 vendors submitted / 4 eligible | ✓ matched exactly |
| 11 candidate groups | ✓ 11 candidate-group rows rendered |
| 1 selected group | ✓ 1 selected group card, auto-expanded and highlighted |
| BUY_TOGETHER | ✓ Decision Hero headline |
| ₹3,732.60 expected savings | ✓ Decision Hero + Key Decision Metrics + Decision Summary |
| Vendor cost shares (₹106.89 / ₹106.89 / ₹141.10 / ₹85.51) | ✓ Vendor Economics bars + table, matching exactly |
| Vendor savings (₹718.11 / ₹1,093.11 / ₹1,046.90 / ₹874.49) | ✓ Vendor Economics table, matching exactly |

None of these numbers are hardcoded anywhere in the new components — they are the harness's fixture data flowing through the exact same, unmodified rendering logic that the live app will use once a real session is available.

## 14. Limitations

- No live, credentialed browser session was available, so an actual sign-in → analyze/reopen → `/results` click-through in the deployed app was not performed (Section 12 explains the mitigating verification that was performed instead).
- `POST /procurement/analyze` never returns a `run_id` (a pre-existing backend characteristic, confirmed in Section 3, not introduced or fixed by this phase per the backend-frozen rule) — a freshly-completed analysis's Results page therefore cannot show a run identifier; only a run reopened from History can, and the header now honestly reflects that distinction rather than fabricating one.
- This page has no fetch of its own, so a "Direct navigation to a valid result" via a bare URL (e.g. pasting a `/results` link) still shows the "No result available" empty state, exactly as before this phase — changing that would require a new backend-facing capability (fetch-by-run-id on this route), which is out of this phase's frozen-backend, no-new-endpoint scope.

## 15. Files Changed

**New:** `frontend/src/components/results/{DecisionHero,ResultMetricGrid,SelectedGroupCard,SelectedGroupNetwork,VendorEconomics,AllocationTable,CandidateGroupsPanel,CandidateGroupRow,DecisionDiagnostics,ResultSummary,ResultActions}.jsx`.
**Modified:** `frontend/src/components/results/{resultHelpers.js,runStatusMeta.js,DecisionExplanation.jsx}`, `frontend/src/pages/ResultsPage.jsx`, `frontend/src/pages/HistoryPage.jsx`, `frontend/src/styles/results.css`.
**Deleted:** `frontend/src/components/results/{ResultsSummary,FinalSelectionSection,SavingsSummary,GroupDecisionList,GroupFormationSummary}.jsx`.
**Untouched:** every backend file, every Supabase/`supabase/` file, `frontend/src/auth/`, `ProtectedRoute`, `AuthContext`, `api/client.js`, `api/procurementApi.js`, the analysis wizard (UI-4), the dashboard (UI-3), the landing page (UI-2), and `components/results/{MetricCard,VendorOutcomesTable}.jsx`.

## 16. Backend Confirmation

**Backend NOT modified. Procurement engine NOT modified.** Confirmed by `git status` (Section shown to the user below): zero changes under `backend/` or `supabase/` beyond what was already present from prior phases before this session began. `python -m pytest -q` remains 178 passed / 0 failed / 0 skipped. No new backend endpoint was created; `POST /procurement/analyze`, `GET /procurement/runs`, and `GET /procurement/runs/{run_id}` are byte-for-byte the same handlers as before this phase.

---

## Implementation Summary

1. **What changed:** `/results` is now a premium "Procurement Decision Cockpit" — Decision Hero → Key Decision Metrics → Selected Procurement Group (+ network diagram) → Vendor Economics (proportional cost-share bars) → Candidate Groups Evaluated (expandable rows) → Diagnostics/Warnings → Vendor Submission Detail → How This Decision Was Reached (numbered pipeline) → Decision Summary → Actions.
2. **Files created:** 11 new components under `components/results/` (Section 15).
3. **Files modified:** `resultHelpers.js`, `runStatusMeta.js`, `DecisionExplanation.jsx`, `ResultsPage.jsx`, `HistoryPage.jsx` (one-line additive: forwards `run_id`/`created_at` it already had), `results.css`.
4. **Files deleted:** 5 superseded components (Section 15), confirmed single-call-site before removal.
5. **Backend changed?** NO.
6. **Procurement engine changed?** NO.
7. **Tests:** 178 passed, 0 failed, 0 skipped (unchanged).
8. **Build:** clean, 163 modules, 0 errors.
9. **Lint:** clean, 0 warnings.
10. **Browser verification:** 5/5 unauthenticated structural checks + 29/29 real-browser checks against real persisted data via a temporary, now-deleted local test harness (Section 12) — genuine Chromium rendering, not a simulation.
11. **Real-data verification:** all real `POTATO_HYD_2026_09` figures (4 vendors, 11 candidates, 1 selected group, BUY_TOGETHER, ₹3,732.60, per-vendor cost shares and savings) matched exactly (Section 13).
12. **Remaining limitations:** no live authenticated click-through was possible in this environment (Section 14); `POST /procurement/analyze`'s lack of a returned `run_id` is a pre-existing backend characteristic, not something this phase could or did change.

**Stopping here per this phase's explicit instruction.** No other page was redesigned, the backend was not touched, nothing was staged or committed (`git add`/`commit`/`push` were never run).
