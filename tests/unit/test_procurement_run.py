"""
Phase 6E tests: application-level orchestration
(backend/services/procurement_run.py).

Covers required test cases T1-T10 (numbering per the Phase 6E task spec).
Every test calls ONLY the public entry point, ProcurementRunService.run --
none manually calls validation/eligibility/compatibility/group-formation/
decision-evaluation/selection directly (T9's own requirement), except the
one test (test_t9_orchestrator_does_not_duplicate_logic) that DELIBERATELY
also calls the underlying Phase 6B/6C/6D services directly, in order to
prove the orchestrator's output matches them exactly rather than computing
anything independently.
"""

from backend.models.run_contracts import ProcurementRunInput, ProcurementRunResult, RunStatus
from backend.services.batch_decision import run_procurement_decision
from backend.services.group_formation import form_candidate_groups
from backend.services.pipeline import evaluate_procurement_context
from backend.services.procurement_run import ProcurementRunService
from tests.fixtures.orchestration_fixtures import (
    ABSTAIN_NO_EVIDENCE,
    COMMODITY,
    COMMODITY_ID,
    CONFIG,
    CONTEXT,
    CONTEXT_DATE,
    ELIGIBLE_1,
    ELIGIBLE_2,
    ELIGIBLE_3,
    FAR_A,
    FAR_B,
    LOW_PRICE_1,
    LOW_PRICE_2,
    OTHER_COMMODITY,
    OTHER_COMMODITY_ID,
    OTHER_CONTEXT,
    VALIDATION_ERROR_NEGATIVE_QTY,
)


def _run(submissions, commodity=COMMODITY, context=CONTEXT, config=CONFIG):
    run_input = ProcurementRunInput(
        commodity=commodity, context=context, vendor_submissions=tuple(submissions), config=config,
    )
    return ProcurementRunService().run(run_input)


# --- T1: full success pipeline ---
def test_t1_full_success_pipeline():
    result = _run([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])

    assert isinstance(result, ProcurementRunResult)
    assert result.eligible_vendor_count == 3
    assert result.abstained_vendor_count == 0
    assert result.validation_error_vendor_count == 0
    assert result.group_formation is not None
    assert result.candidate_group_count > 0
    assert result.final_selection is not None
    # At least one group reaches the final result.
    assert result.selected_group_count >= 1
    assert result.run_status == RunStatus.COMPLETED.value


# --- T2: mixed vendor outcomes ---
def test_t2_mixed_vendor_outcomes_pipeline_continues_for_eligible():
    result = _run([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3, ABSTAIN_NO_EVIDENCE, VALIDATION_ERROR_NEGATIVE_QTY])

    assert result.eligible_vendor_count == 3
    assert result.abstained_vendor_count == 1
    assert result.validation_error_vendor_count == 1
    # The pipeline still ran for the 3 eligible vendors.
    assert result.group_formation is not None
    assert result.candidate_group_count > 0
    assert result.final_selection is not None
    assert result.selected_group_count >= 1
    assert result.run_status == RunStatus.COMPLETED_WITH_ABSTENTIONS.value

    abstained_ids = {v.vendor_id for v in result.batch_eligibility.abstained_vendors}
    error_ids = {v.vendor_id for v in result.batch_eligibility.validation_error_vendors}
    assert abstained_ids == {"ABSTAIN_NO_EVIDENCE"}
    assert error_ids == {"VALIDATION_ERROR_NEGATIVE_QTY"}


# --- T3: zero eligible vendors ---
def test_t3_zero_eligible_vendors():
    result = _run([ABSTAIN_NO_EVIDENCE, VALIDATION_ERROR_NEGATIVE_QTY])

    assert result.eligible_vendor_count == 0
    assert result.group_formation is None
    assert result.final_selection is None
    assert result.candidate_group_count == 0
    assert result.selected_group_count == 0
    assert result.run_status == RunStatus.COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS.value


# --- T4: one eligible vendor ---
def test_t4_one_eligible_vendor():
    result = _run([ELIGIBLE_1])

    assert result.eligible_vendor_count == 1
    assert result.group_formation is None
    assert result.final_selection is None
    assert result.run_status == RunStatus.COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS.value


# --- T5: no compatible vendors ---
def test_t5_no_compatible_vendors():
    result = _run([FAR_A, FAR_B])

    assert result.eligible_vendor_count == 2
    assert result.group_formation is not None
    assert result.candidate_group_count == 0
    assert result.final_selection is None
    assert result.selected_group_count == 0
    assert result.run_status == RunStatus.COMPLETED_NO_GROUPS.value
    assert set(result.group_formation.singleton_vendor_ids) == {"FAR_A", "FAR_B"}


# --- T6: candidates exist but none become BUY_TOGETHER ---
def test_t6_candidates_exist_but_none_buy_together():
    result = _run([LOW_PRICE_1, LOW_PRICE_2])

    assert result.eligible_vendor_count == 2
    assert result.group_formation is not None
    assert result.candidate_group_count > 0
    assert result.final_selection is not None
    assert result.selected_group_count == 0
    assert result.final_selection.selected_group_ids == ()
    assert result.run_status == RunStatus.COMPLETED_NO_SELECTION.value


# --- T7: commodity isolation ---
def test_t7_commodity_isolation():
    submissions = [ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3]

    result_a = _run(submissions, commodity=COMMODITY, context=CONTEXT, config=CONFIG)
    result_b = _run(submissions, commodity=OTHER_COMMODITY, context=OTHER_CONTEXT, config=CONFIG)

    assert result_a.commodity_id == COMMODITY_ID
    assert result_a.context_date == CONTEXT_DATE
    assert result_b.commodity_id == OTHER_COMMODITY_ID
    assert result_b.batch_eligibility.context.commodity_id == OTHER_COMMODITY_ID
    # Each run's own embedded results are tagged with only its own
    # commodity -- no cross-contamination between the two independent runs.
    assert result_a.group_formation.commodity_id == COMMODITY_ID
    assert result_b.group_formation.commodity_id == OTHER_COMMODITY_ID


# --- T8: traceability ---
def test_t8_traceability_preserves_every_stage():
    result = _run([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3, ABSTAIN_NO_EVIDENCE, VALIDATION_ERROR_NEGATIVE_QTY])

    # Vendor outcomes (Phase 6B) -- reason codes and provenance preserved.
    abstained = result.batch_eligibility.abstained_vendors[0]
    assert abstained.reason_code == "INSUFFICIENT_DEMAND_EVIDENCE"
    error = result.batch_eligibility.validation_error_vendors[0]
    assert error.reason_code is not None
    eligible = result.batch_eligibility.eligible_vendors[0]
    assert eligible.demand_provenance is not None

    # Group formation (Phase 6C) -- pools and candidates inspectable.
    assert len(result.group_formation.pools) >= 1
    assert len(result.group_formation.candidate_groups) > 0

    # Candidate evaluation / WAIT-EXPAND (Phase 6D) -- base decision, final
    # state, and reasons all preserved on every evaluated candidate.
    for evaluated in result.final_selection.all_evaluated_results:
        assert evaluated.decision.reason  # never blank
        assert evaluated.final_decision_state  # always set

    # Final selection (Phase 6D) -- savings and coverage inspectable.
    assert result.final_selection.total_savings_rs >= 0
    assert result.final_selection.total_vendor_coverage >= 0


# --- T9: no logic duplication ---
def test_t9_orchestrator_does_not_duplicate_logic():
    submissions = [ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3]
    run_input = ProcurementRunInput(
        commodity=COMMODITY, context=CONTEXT, vendor_submissions=tuple(submissions), config=CONFIG,
    )

    orchestrated = ProcurementRunService().run(run_input)

    # Independently call the real Phase 6B -> 6C -> 6D services directly,
    # exactly as they were called before Phase 6E existed.
    batch_eligibility = evaluate_procurement_context(CONTEXT, list(submissions))
    eligible_inputs = [r.vendor_input for r in batch_eligibility.eligible_vendors]
    formation = form_candidate_groups(eligible_inputs, COMMODITY_ID, CONTEXT_DATE, CONFIG.d_max_km)
    direct_selection = run_procurement_decision(formation, COMMODITY, CONTEXT, CONFIG)

    assert orchestrated.candidate_group_count == len(formation.candidate_groups)
    assert orchestrated.final_selection.selected_group_ids == direct_selection.selected_group_ids
    assert orchestrated.final_selection.total_savings_rs == direct_selection.total_savings_rs
    assert orchestrated.final_selection.total_vendor_coverage == direct_selection.total_vendor_coverage


# --- Additional: invalid context (empty vendor collection) ---
def test_invalid_context_short_circuits_before_any_vendor_processing():
    result = _run([])

    assert result.run_status == RunStatus.COMPLETED_INVALID_CONTEXT.value
    assert result.batch_eligibility.context_validation.is_valid is False
    assert result.eligible_vendor_count == 0
    assert result.group_formation is None
    assert result.final_selection is None
