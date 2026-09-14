# Phase 6E — End-to-End Procurement Orchestration Layer

**Date:** 2026-09-14
**Scope:** A single application-level orchestration entry point that sequences the already-implemented Phase 6B (validation/demand/eligibility) → Phase 6C (compatibility/group formation) → Phase 6D (candidate evaluation/WAIT-EXPAND/overlap resolution/selection) pipeline for one procurement run, and assembles their outputs into one structured, fully-traceable result. No new mathematical, validation, or decision logic; no API, database, or frontend.

---

## 1. Purpose

Prior phases each own one authoritative stage of the pipeline but none owns *running the whole thing*. A caller wanting a complete procurement analysis had to know, in order, to call `pipeline.evaluate_procurement_context`, then `group_formation.form_candidate_groups`, then `batch_decision.run_procurement_decision`, and to handle every early-exit case (invalid context, too few eligible vendors, no candidate groups) itself. Phase 6E provides exactly one call — `ProcurementRunService.run(ProcurementRunInput)` — that does this sequencing and returns one structured `ProcurementRunResult`, so no future caller (a future API, script, or test) needs to re-derive the correct stage order or its stop conditions.

## 2. Existing Modules Reused

Inspected directly before writing any code:

| Component | Reused as-is |
|---|---|
| `backend.services.pipeline.evaluate_procurement_context` | ✅ Called once, unmodified — Phase 6E does **not** call `validation.py` or `eligibility.py` directly, since that would be a second, competing orchestration of steps this function already sequences correctly |
| `backend.services.group_formation.form_candidate_groups` | ✅ Called once, unmodified |
| `backend.services.batch_decision.run_procurement_decision` | ✅ Called once, unmodified (itself sequencing Phase 6D's `decision_evaluation.evaluate_candidate_groups` and `selection.select_final_groups`, untouched) |
| `BatchEligibilityResult`, `VendorSubmission`, `CommodityParams`, `ProcurementContext`, `ConfigParams` | ✅ Reused verbatim in `ProcurementRunInput`/`ProcurementRunResult` — no second vendor, context, or config schema |
| `GroupFormationResult`, `FinalSelectionResult` | ✅ Embedded unchanged inside `ProcurementRunResult` — not flattened, not re-derived |

Confirmed by inspection: no file under `backend/core/`, `backend/services/decision_engine.py`, `backend/services/group_formation.py`, `backend/services/decision_evaluation.py`, `backend/services/selection.py`, `backend/services/validation.py`, or `backend/services/eligibility.py` is imported for its *logic* by the new Phase 6E files beyond the three top-level entry-point calls named above.

## 3. Orchestration Architecture

One class, `ProcurementRunService`, in `backend/services/procurement_run.py`, with one public method, `run(run_input: ProcurementRunInput) -> ProcurementRunResult`. The method body is a linear sequence of stage calls with early-return stop conditions — no branching logic re-decides anything a prior phase already decided; it only decides *whether to proceed to the next stage* based on the prior stage's own output (e.g., `len(eligible_vendor_inputs) < 2`, `len(group_formation.candidate_groups) == 0`). A private `_assemble` static method builds the final `ProcurementRunResult`, computing only plain `len()` counts from the embedded collections — never independent data.

## 4. Exact Pipeline Sequence

```
ProcurementRunInput
  → pipeline.evaluate_procurement_context(context, vendor_submissions)     [Phase 6B]
      → if context invalid:                    STOP → COMPLETED_INVALID_CONTEXT
      → if eligible_vendors < 2:                STOP → COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS
  → group_formation.form_candidate_groups(eligible VendorInputs, ...)      [Phase 6C]
      → if candidate_groups == 0:               STOP → COMPLETED_NO_GROUPS
  → batch_decision.run_procurement_decision(formation, commodity, ...)     [Phase 6D]
      (internally: decision_evaluation.evaluate_candidate_groups → resolve_wait_or_expand
                   → selection.select_final_groups)
      → if selected_group_ids == ():             COMPLETED_NO_SELECTION
      → elif any abstained/validation-error vendor: COMPLETED_WITH_ABSTENTIONS
      → else:                                     COMPLETED
  → ProcurementRunResult
```

This exactly matches the required Step 1–11 order; no step was reordered, skipped, or merged.

## 5. Run-Level Input Contract

`ProcurementRunInput` (`backend/models/run_contracts.py`):

```python
commodity: CommodityParams
context: ProcurementContext
vendor_submissions: Tuple[VendorSubmission, ...]
config: ConfigParams
```

One run represents exactly `(commodity, context, vendor universe)`, per Phase 5E's own definition. `config` carries `d_max_km` (Phase 6C) alongside `trader_margin`/`transport_tiers` (Phase 6D) — Phase 6A's existing `ConfigParams` already bundles exactly what both downstream stages need, so it is reused whole rather than split into two overlapping new shapes.

## 6. Run-Level Output Contract

`ProcurementRunResult` embeds each phase's own unmodified output object rather than re-shaping it:

- `batch_eligibility: BatchEligibilityResult` — Phase 6B's full result (context validation, eligible/abstained/validation-error vendor lists, each with reason codes and demand provenance).
- `group_formation: Optional[GroupFormationResult]` — Phase 6C's full result (pools, candidate groups, singleton vendors, diagnostics), or `None` if group formation was never attempted.
- `final_selection: Optional[FinalSelectionResult]` — Phase 6D's full result (every evaluated candidate with base + final decision state, resolving superset info, selected groups, total savings, vendor coverage, tie-break note), or `None` if selection was never attempted.
- Plain derived counts (`total_vendors_submitted`, `eligible_vendor_count`, `abstained_vendor_count`, `validation_error_vendor_count`, `candidate_group_count`, `selected_group_count`) — each one a `len()` of an embedded collection, computed once at assembly time.
- `run_status`, `commodity_id`, `context_date`.

No field here duplicates or competes with a field already defined in Phase 6A/6B/6C/6D's own contracts.

## 7. Run-Level Statuses

`RunStatus` (new enum, `backend/models/run_contracts.py`), assigned by strict precedence (first-applicable wins) — documented in full in `procurement_run.py`'s module docstring:

| Order | Status | Condition |
|---|---|---|
| 1 | `COMPLETED_INVALID_CONTEXT` | `context_validation.is_valid` is `False` |
| 2 | `COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS` | fewer than 2 eligible vendors |
| 3 | `COMPLETED_NO_GROUPS` | 2+ eligible vendors, but zero candidate groups formed |
| 4 | `COMPLETED_NO_SELECTION` | candidate groups existed, but none were finally selected |
| 5 | `COMPLETED_WITH_ABSTENTIONS` | ≥1 group selected, but ≥1 vendor abstained or had a validation error |
| 6 | `COMPLETED` | ≥1 group selected, every submitted vendor was eligible |

This is a **new**, Phase 6E-owned concept — it never reuses or is confused with vendor-level `OutcomeKind` (OK/ABSTAIN/VALIDATION_ERROR) or group-level `DecisionState` (BUY_TOGETHER/etc.), per the explicit instruction not to merge these. The precedence choice (stage-outcome takes priority over the abstention flag) is a documented design decision, not an oversight: abstention/validation-error counts remain fully visible on the result regardless of which status wins, via `batch_eligibility` and the `*_count` fields.

## 8. Vendor-Level Outcome Handling

No new vendor-outcome shape was created. `batch_eligibility.eligible_vendors` / `.abstained_vendors` / `.validation_error_vendors` are exactly Phase 6B's own `VendorEligibilityResult` list, carrying `vendor_id`, `status`, `eligible`, `vendor_input` (with `estimation_provenance`), `reason_code`, `reason_detail` — untouched. Phase 6B's own per-vendor isolation (one vendor's structural error never stops another vendor's processing) is inherited automatically, since `evaluate_procurement_context` is called exactly once and already guarantees it internally.

## 9. Pipeline Stop Conditions

All six required cases (A–F) are handled:

| Case | Behavior confirmed by |
|---|---|
| A: 0 eligible vendors | `test_t3_zero_eligible_vendors` |
| B: 1 eligible vendor | `test_t4_one_eligible_vendor` |
| C: 2+ eligible, no compatibility | `test_t5_no_compatible_vendors` |
| D: candidates exist, none BUY_TOGETHER | `test_t6_candidates_exist_but_none_buy_together` |
| E: some abstain, others eligible | `test_t2_mixed_vendor_outcomes_pipeline_continues_for_eligible` |
| F: some validation errors, others eligible | `test_t2_mixed_vendor_outcomes_pipeline_continues_for_eligible` (combined with E) |

An additional, not separately required, case (empty vendor collection → structurally invalid context) is covered by `test_invalid_context_short_circuits_before_any_vendor_processing`.

## 10. Traceability Design

Every embedded object retains its own stage's full reasoning: `batch_eligibility` retains reason codes/detail per vendor; `group_formation` retains pools and every candidate's `source_pool_id`/`pool_vendor_ids`; `final_selection.all_evaluated_results` retains, per candidate, the unmutated base `GroupDecisionResult.reason`, the refined `final_decision_state`, `resolving_superset_group_ids`, and `expansion_reason`. Nothing is flattened away. `selection.explain()` (Phase 6D, untouched) remains available to a future caller for human-readable text per candidate — Phase 6E does not redesign or duplicate it, and does not build any new explanation generator (`test_t8_traceability_preserves_every_stage` confirms every evaluated candidate carries a non-blank reason).

## 11. Test Scenarios

`tests/fixtures/orchestration_fixtures.py` provides `VendorSubmission` fixtures (not pre-resolved `VendorInput`) since Phase 6E's whole point is running the real Phase 6B step, not bypassing it: three mutually-compatible, economically-favorable vendors (`ELIGIBLE_1/2/3`), one no-evidence vendor (`ABSTAIN_NO_EVIDENCE`), one malformed vendor (`VALIDATION_ERROR_NEGATIVE_QTY`), two geographically mutually-incompatible eligible vendors (`FAR_A`/`FAR_B`), and two compatible-but-economically-unfavorable vendors (`LOW_PRICE_1/2`). T1–T10 (plus one bonus invalid-context test) are implemented in `tests/unit/test_procurement_run.py`.

## 12. Test Results

```
10 new tests passed, 0 failed, 0 skipped
93 total: passed, 0 failed, 0 skipped
```

| Suite | Tests | Result |
|---|---|---|
| Phase 6A (unchanged) | 20 | ✅ all pass |
| Phase 6B (unchanged) | 21 | ✅ all pass |
| Phase 6C (unchanged) | 22 | ✅ all pass |
| Phase 6D (unchanged) | 20 | ✅ all pass |
| Phase 6E — `test_procurement_run.py` | 10 | ✅ all pass |
| **Total** | **93** | **93 passed, 0 failed, 0 skipped** |

No failure was hidden; no test was skipped or modified to force a pass.

## 13. Files Created

- `backend/models/run_contracts.py` — `RunStatus`, `ProcurementRunInput`, `ProcurementRunResult`
- `backend/services/procurement_run.py` — `ProcurementRunService`
- `tests/fixtures/orchestration_fixtures.py`
- `tests/unit/test_procurement_run.py`
- This report

## 14. Files Modified

**None.** No file under `backend/core/`, `backend/models/contracts.py`, `backend/models/batch_contracts.py`, `backend/models/decision_contracts.py`, `backend/models/group_formation_contracts.py`, `backend/services/pipeline.py`, `backend/services/validation.py`, `backend/services/eligibility.py`, `backend/services/group_formation.py`, `backend/services/decision_evaluation.py`, `backend/services/selection.py`, `backend/services/batch_decision.py`, or any existing test/report was changed. No blocking interface problem was encountered — every required capability already existed with the exact shape Phase 6E needed.

## 15. Scope Verification

No cost/savings/MOQ/freshness/allocation formula, no Haversine, no compatibility graph, no subset enumeration, no WAIT/EXPAND logic, no overlap optimization was reimplemented — confirmed by inspection: `procurement_run.py` imports only the three top-level entry points named in Section 2, plus the new `run_contracts` module. No new dependency was installed (`requirements.txt` unchanged). No API, database, persistent logging, frontend, authentication, real-time data acquisition, autonomous ordering, or ML code exists anywhere in this phase's new files. The closed Potato ML experiment and its underlying data were not read or touched.

## 16. Known Limitations

Phase 6E does **not** implement: an HTTP/API layer, a database or persistence layer, persistent structured logging, a frontend, authentication/authorization, real-time market-data acquisition, autonomous/automatic ordering execution, or any machine-learning component. `ProcurementRunService.run` is a single, synchronous, in-memory call — it does not batch multiple procurement contexts, does not cache results across calls, and (deliberately, per its own docstring) does not catch exceptions raised by Phase 6C/6D's pure computations, since doing so would risk disguising a genuine defect as a normal run status. These are all explicitly out of this phase's scope, to be addressed only in a future, separately-authorized phase.

---

**Files read for this phase:** `backend/services/pipeline.py`, `backend/services/validation.py`, `backend/services/eligibility.py`, `backend/services/group_formation.py`, `backend/services/decision_evaluation.py`, `backend/services/selection.py`, `backend/services/batch_decision.py`, `backend/models/contracts.py`, `backend/models/batch_contracts.py`, `backend/models/reasons.py`, `backend/models/decision_contracts.py`, `backend/models/group_formation_contracts.py`, `reports/phase6a_core_foundation_report.md`, `reports/phase6b_validation_and_eligibility_report.md`, `reports/phase6c_group_formation_report.md`, `reports/phase6d_procurement_decision_and_selection.md`.
**Files modified:** none outside the new `backend/`, `tests/` additions, and this report.
