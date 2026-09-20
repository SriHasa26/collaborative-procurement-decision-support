# Phase 7E — Procurement Results Dashboard

**Date:** 2026-09-14
**Scope:** Transform `ResultsPage` from Phase 7D's minimal handoff message into a complete, transparent Procurement Decision Dashboard that displays the real backend response. No backend changes, no recalculated decisions, no History integration.

---

## 1. Phase Objective

Phase 7D could receive a real backend response and hand it to `/results`, but displayed almost nothing. Phase 7E's job is to render that response completely and honestly: run status, vendor outcomes, candidate group decisions, the final selection, savings, and a static explanation of the pipeline — using only fields the backend actually returns, and never recomputing a decision, savings figure, or distance in the frontend.

## 2. Existing Backend Response Structure Inspected

**Files read this phase:** `backend/models/run_contracts.py`, `backend/models/batch_contracts.py`, `backend/models/group_formation_contracts.py`, `backend/models/decision_contracts.py`, `backend/models/contracts.py` (for `GroupDecisionResult`/`PerVendorAllocation`), `backend/models/enums.py`, `backend/api/routes/procurement.py`, `backend/api/serialization.py`, plus Phase 7D's `AnalysisForm.jsx`/`ResultsPage.jsx`.

**Actual response generated and inspected directly** (Step 1's explicit instruction) by running the real, unmodified pipeline (`ProcurementRunService().run(...)` → `to_json_safe(...)`) with a 7-vendor scenario chosen to exercise every code path in one response: `BUY_TOGETHER` (the full 5-vendor group), `WAIT_OR_EXPAND_GROUP` (multiple subsets, later resolved by that same group), `DO_NOT_BUY_TOGETHER`, `ABSTAIN` (a vendor with no demand evidence), and `VALIDATION_ERROR` (a vendor with a negative diary quantity).

Confirmed top-level shape (`ProcurementRunResult`):
```
run_status, commodity_id, context_date,
total_vendors_submitted, eligible_vendor_count, abstained_vendor_count,
validation_error_vendor_count, candidate_group_count, selected_group_count,
batch_eligibility, group_formation (nullable), final_selection (nullable)
```
`batch_eligibility.{eligible,abstained,validation_error}_vendors[]` each carry `vendor_id, status ("OK"/"ABSTAIN"/"VALIDATION_ERROR"), eligible, vendor_input (nullable), demand_provenance (nullable), reason_code (nullable), reason_detail`. `group_formation.{pools, candidate_groups, singleton_vendor_ids, diagnostics}`. `final_selection.{selected_group_ids, selected_results, non_selected_buy_together_results, wait_or_expand_results, do_not_buy_results, abstained_results, all_evaluated_results, total_savings_rs, total_vendor_coverage, tie_break_note}` — each "result" entry is an `EvaluatedGroupResult`: `{decision (a full GroupDecisionResult), final_decision_state, commodity_id, context_date, source_pool_id, pool_vendor_ids, vendor_ids, resolving_superset_group_ids, expansion_reason}`. `decision` carries `group_id, decision_state, reason, k_star, aggregate_quantity_kg, moq_applicable, moq_met, moq_shortfall_kg, centroid_distance_km, within_d_max, individual_cost_total_rs, collaborative_cost_rs, savings_rs, per_vendor_allocation (nullable list of {vendor_id, share_rs, individual_savings_rs, consumption_time_days})`.

Every field name used anywhere in the new frontend code traces directly to this inspected structure — none was guessed.

## 3. Results Information Architecture

Sections A–G, in order, exactly as specified, each mapped to real fields:

| Section | Backend source |
|---|---|
| A. Run Summary | top-level `run_status` + the six `*_count`/`total_vendors_submitted` fields |
| B. Final Decision | `final_selection.selected_results` |
| C. Savings Summary | `final_selection.total_savings_rs`, `.total_vendor_coverage`, `.tie_break_note` |
| D. Vendor Outcomes | `batch_eligibility.{eligible,abstained,validation_error}_vendors` |
| E. Group Decisions | `final_selection.all_evaluated_results` |
| F. Group Formation Summary | `group_formation.{pools, candidate_groups, singleton_vendor_ids}` |
| G. Explanation / Transparency | static content (no backend data) |

## 4. Components Created

All under `frontend/src/components/results/`:

| File | Purpose |
|---|---|
| `resultHelpers.js` | Pure formatting/safe-accessor functions (Section 24) |
| `runStatusMeta.js` | Fixed label/color mapping for the 6 real `RunStatus` values (mirrors `decisionStateMeta.js`'s existing pattern) |
| `MetricCard.jsx` | One summary metric in a Card |
| `ResultsSummary.jsx` | Section A |
| `FinalSelectionSection.jsx` | Section B (includes an inline `AllocationTable` for per-vendor savings) |
| `SavingsSummary.jsx` | Section C |
| `VendorOutcomesTable.jsx` | Section D |
| `GroupDecisionList.jsx` | Section E |
| `GroupFormationSummary.jsx` | Section F |
| `DecisionExplanation.jsx` | Section G |

**Deliberately not created**, per "create only components that genuinely improve maintainability": a separate `VendorOutcomeRow.jsx` / `GroupDecisionCard.jsx` (both sections render as compact tables — more appropriate than a card-per-row for up to dozens of groups — with row content simple enough to inline in each table's `.map()`), and `ResultsEmptyState.jsx` (the existing `EmptyState`/`ErrorState` components already cover both the direct-visit and malformed-response cases with no new component needed). No `frontend/src/utils/` folder was created — the only shared logic is results-specific and lives in `resultHelpers.js`, colocated with its consumers.

## 5. Components Reused

`Card`, `Badge`, `StatusBadge` (via `runStatusMeta`'s variant naming, consistent with it), `DecisionStateBadge`, `EmptyState`, `ErrorState`, `Button`, `PageHeader` — all Phase 7B, all unmodified. `history-table`/`history-table-wrapper` CSS classes (Phase 7B, originally built for the History page's empty table) are reused for the Vendor Outcomes and Group Decisions tables rather than inventing new table styling.

## 6. How Run Status Is Displayed

`ResultsSummary.jsx` reads `result.run_status` (a real `RunStatus` string) and looks it up in `runStatusMeta.js`'s fixed table — one of the 6 actual enum values from `backend/models/run_contracts.py`, each mapped to a short label and a `Badge` color. No `danger` variant is used for any run status (Section 24) — every one is a genuinely successful HTTP 200 response (Phase 7D Section 9), including `COMPLETED_INVALID_CONTEXT`. An unrecognized value (should never occur) falls back to displaying the raw string rather than guessing a label.

## 7. How Vendor Outcomes Are Displayed

`VendorOutcomesTable.jsx` concatenates the three existing arrays (`getVendorOutcomes()`, presentation-only aggregation) into one table: Vendor ID, Outcome badge, Demand provenance, Location status, and the backend's own `reason_detail` sentence verbatim — no new explanation text is generated.

## 8. How VALIDATION_ERROR Differs From ABSTAIN

Rendered with distinct badge variants and distinct labels, directly from each vendor's own `status` field (`OutcomeKind`): `ABSTAIN` → **"Abstained"**, `info` (indigo) variant — the same neutral, non-error palette `DecisionStateBadge` already uses for the group-level `ABSTAIN` decision state, deliberately never `danger`. `VALIDATION_ERROR` → **"Validation error"**, `danger` (red) variant — genuinely distinct, since it represents malformed input, not insufficient evidence. The two are never merged into one label or color anywhere in the dashboard.

## 9. How Group Decisions Are Displayed

`GroupDecisionList.jsx` renders every entry in `final_selection.all_evaluated_results` (26 in the inspected sample) as one table row: Group ID, vendor list, **base** decision (`decision.decision_state` — Phase 6A's original, never-mutated evaluation) and **final** decision (`final_decision_state` — after Phase 6D's WAIT/EXPAND resolution) as two separate `DecisionStateBadge`s side by side, savings, and an explanation column. Rows are sorted (display-only, via `sortEvaluatedGroups`) with selected groups first, then by decision-state priority, then alphabetically by group ID — this changes only row *order*, never which state a group shows.

## 10. How WAIT_OR_EXPAND_GROUP Is Represented

For any row whose `final_decision_state` is `WAIT_OR_EXPAND_GROUP`, the explanation column shows the backend's own `expansion_reason` text, and — if `resolving_superset_group_ids` is non-empty — a second line "Resolved by: `<group ids>`", listing exactly the already-generated superset group IDs the backend identified. No new expansion/resolution computation happens in the frontend; every value shown was already present in the response.

## 11. How Savings Are Displayed

Two places, both reading `final_selection.total_savings_rs` **directly** (Section C's `SavingsSummary`, and each selected group's own `decision.savings_rs` in Section B) — **never** re-summed from individual group savings in JavaScript. This is a deliberate choice, documented in `SavingsSummary.jsx`'s own header comment: the backend (`backend/services/selection.py`) already computes this sum authoritatively; re-deriving the same number client-side would only add a risk of silent drift from the backend's value with no benefit. `formatCurrency()` (frontend-only number formatting, e.g. `₹1,840.00`) is the only transformation applied. Per-vendor amounts in the `AllocationTable` come directly from `decision.per_vendor_allocation`. When no group is selected, no `₹0.00` is shown as a false "success" figure — a plain sentence explains that no collaborative savings apply for this run.

## 12. Direct `/results` Behavior

Unchanged in mechanism from Phase 7D: `useLocation().state?.result` is read; if absent, the existing `EmptyState` + "Start New Analysis" button (→ `/analyze`) renders, with no API call and no history query. Verified via the real running dev server (route returns `200` with the correct shell; the empty-state branch is a pure client-side render with no data dependency, identical in mechanism to what Phase 7D already proved works).

## 13. Missing/Empty Result Handling

`hasUsableResult(result)` checks only `Boolean(result) && typeof result.run_status === "string"`. Three cases: (a) no `location.state.result` at all → the Step-12 empty state; (b) a `result` object present but failing this check → a distinct `ErrorState` ("Unexpected response... please try running the analysis again"), never a raw JavaScript exception; (c) a usable result → the full dashboard, itself built entirely from optional-chaining/`??` defaults (`result.final_selection?.selected_results ?? []`, `result.group_formation?.pools ?? []`, etc.) so a legitimately-`null` `group_formation`/`final_selection` (confirmed real for `COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS`/`COMPLETED_NO_GROUPS`, Section 14) renders safe explanatory text instead of crashing.

## 14. Real Backend Integration Verification

**Actually verified**, using the same technique validated in Phase 7D (Vite's `ssrLoadModule`, running the real, unmodified `frontend/src/api/procurementApi.js` and the real, unmodified new `resultHelpers.js`/`runStatusMeta.js` against a real running backend — not a reimplementation, not a mock):

- Started the real backend (`uvicorn`, port 8731) and the real Vite dev server (port 5174, 5173 was already in use by an unrelated local process) — `GET /health` → `200`; all 5 routes (`/`, `/analyze`, `/results`, `/history`, unknown route) → `200`; `ResultsPage.jsx` and all new `components/results/*` files transformed with no error markers.
- Built a real, valid 7-vendor payload with the real Phase 7C `buildAnalysisPayload()`/`validateAnalysisForm()`, submitted it via the real `analyzeProcurement()` — received `run_status: "COMPLETED_WITH_ABSTENTIONS"` with a genuine mix of `BUY_TOGETHER`/`WAIT_OR_EXPAND_GROUP`/`DO_NOT_BUY_TOGETHER`/`ABSTAIN`/`VALIDATION_ERROR` outcomes in one response.
- Ran the real `resultHelpers.js` functions against this real response: `hasUsableResult` correctly `true` for the real result and `false` for `null`/`{}`; `getVendorOutcomes` returned all 7 vendors with correct statuses (`V1..V7: OK`, `ABSTAIN_1: ABSTAIN`, `VALERR_1: VALIDATION_ERROR`); `sortEvaluatedGroups` returned all 26 evaluated groups with the selected `BUY_TOGETHER` group correctly ordered first; `formatCurrency` correctly rendered `₹1,840.00` / `—` (null) / `-₹50.00` (negative); `getRunStatusMeta` correctly mapped the real status and safely fell back for an invented one.
- Submitted a second real request with a single vendor to obtain a genuine `COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS` response (`group_formation: null`, `final_selection: null`, confirmed directly) and re-ran the exact expressions every affected component uses (`final_selection?.selected_results ?? []`, etc.) against it — all resolved to safe empty results, no exception.
- **Persistence confirmed**: direct SQLite inspection of `data/app/procurement.db` showed the row count increase from 4 → 6 across these two real submissions, with the correct `commodity`/`run_status` values for each.
- Both dev processes were stopped cleanly after verification.

**Not verified:** no literal browser DOM render/click-through was performed (no headless-browser tool installed, consistent with every prior frontend phase's documented limitation). What was verified instead — every helper function and the real API layer executing against real backend responses covering all five decision states and both a populated and a fully-null `group_formation`/`final_selection` case — is the strongest non-browser verification available and directly exercises the exact data every dashboard component reads.

## 15. Build Result

```
npm run build -> PASS (74 modules transformed, zero errors)
```

## 16. Lint Result

```
npm run lint (oxlint) -> PASS, zero warnings
```

## 17. Backend Test Result

```
pytest -q -> 122 passed, 0 failed, 0 skipped
```
Unchanged from the pre-Phase-7E baseline.

## 18. Files Created

`frontend/src/components/results/{resultHelpers.js, runStatusMeta.js, MetricCard.jsx, ResultsSummary.jsx, FinalSelectionSection.jsx, SavingsSummary.jsx, VendorOutcomesTable.jsx, GroupDecisionList.jsx, GroupFormationSummary.jsx, DecisionExplanation.jsx}` (10 files), `frontend/src/styles/results.css`, this report.

## 19. Files Modified

`frontend/src/pages/ResultsPage.jsx` (full rewrite: Phase 7D's minimal handoff message replaced with the composed dashboard; the direct-visit empty state and the refresh-limitation documentation are carried forward, not removed), `frontend/src/main.jsx` (added the `results.css` import).

## 20. Files Deleted

None.

## 21. Dependencies Added

**None.** `frontend/package.json` is unchanged. The Group Formation Summary's collapsible pool list uses the native `<details>`/`<summary>` HTML element — zero-dependency, no new package.

## 22. Bugs Found and Fixes

One minor authoring slip, caught and fixed before verification: `GroupDecisionList.jsx` initially had two separate `import { X } from "./resultHelpers"` statements for `formatCurrency` and `sortEvaluatedGroups`; merged into one import. No functional bug — caught during review, not by a failing check. No backend-side issues were found.

**No blocking problems found.**

## 23. Known Limitations

No literal browser-rendered verification was performed (Section 14). The Group Decisions table can be long for a large candidate pool (26 rows in the inspected example; Phase 2B's own documented ~5–20 vendor scope keeps this bounded, and rows are sorted so the selected/most-relevant groups appear first) — no pagination or virtualization was added, since none was requested and the existing scope doesn't need it. The dashboard has no way to re-fetch or refresh a result after a page reload (the same navigation-state limitation Phase 7D already documented) — persistent retrieval by run ID is explicitly deferred to a later History-integration phase.

## 24. Confirmation: No Backend Decision Logic Was Duplicated

Confirmed by design and by inspection: every displayed decision state, savings figure, distance, MOQ/freshness/WAIT-EXPAND outcome, and eligibility classification is read directly from a backend response field, never computed, inferred, or overridden in React. `resultHelpers.js`'s own header comment states this boundary explicitly, and every function in it was reviewed against that rule: `formatCurrency`/`formatNumber`/`formatDistance` only format already-computed numbers; `hasUsableResult` only checks presence of a field; `getVendorOutcomes` only concatenates three already-existing arrays; `sortEvaluatedGroups` only reorders already-existing entries for display, never changing a `decision_state` value. No `if (savings > 0)` or equivalent decision-making pattern exists anywhere in the new code (confirmed by inspection — no new file computes a boolean from `savings_rs`, `moq_met`, or any cost field to decide a label).

## 25. Confirmation: Phase 7F Was NOT Started

Confirmed. No History-page integration (`getProcurementRuns()`/`getProcurementRun()` remain uncalled from any page), no run-detail retrieval by ID, no authentication, no Supabase/Firebase, no database migration, no user accounts, no deployment configuration. `git status --short backend/ requirements.txt` returned no output — zero backend files changed this phase.

---

**Files read for this phase:** see Section 2.
**Files created:** see Section 18. **Files modified:** see Section 19. **Files deleted:** none.
