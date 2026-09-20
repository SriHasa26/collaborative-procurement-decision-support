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

from backend.api.schemas import ProcurementAnalysisRequest, build_run_input
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


# --- Regression: the real, historically-persisted POTATO_HYD_2026_09 run ---
# A bug report once claimed this scenario had regressed to DO_NOT_BUY_TOGETHER
# after a frontend redesign. Investigation (through the actual UI via
# Playwright, capturing the real POST /procurement/analyze payload) proved
# the frontend payload builder and this service are both byte-for-byte
# unchanged and correct; the "regression" was two mis-transcribed values in
# the bug report itself (wholesale_price of 12 instead of the real -4, and
# GUDIMALKAPUR_POTATO_01's demand of 30 instead of the real 33 kg/day),
# confirmed against the actual persisted run's stored input/result JSON.
# This test locks in the real historical input -> the real historical
# result (4 vendors, 11 candidate groups, BUY_TOGETHER, Rs 3,732.60 savings)
# so a *genuine* future change to compatibility/economics/selection would be
# caught here, rather than being confused with this kind of data-entry drift
# again. Goes through ProcurementAnalysisRequest/build_run_input (the same
# API schema layer backend/api/routes/procurement.py uses), not a hand-built
# ProcurementRunInput, so it also guards the request-schema conversion.
def test_potato_hyd_2026_09_known_good_scenario_matches_historical_baseline():
    payload = {
        "commodity": {"commodity_id": "POTATO_HYD_2026_09", "freshness_window_days": 7, "moq_kg": 50},
        "context": {
            "commodity_id": "POTATO_HYD_2026_09",
            "date": "2026-09-13",
            "wholesale_price": {"value_rs_per_kg": -4.0, "geographic_level": "MANDI_LEVEL"},
        },
        "vendor_submissions": [
            {
                "vendor_id": "BOWENPALLY_POTATO_01",
                "location": {"status": "VENDOR_SPECIFIC_APPROXIMATE", "lat": 17.469245, "lon": 78.494895},
                "individual_price_rs_per_kg": 11,
                "practical_horizon_days": 3,
                "user_provided_q_i": 25,
                "diary_records": None,
                "peer_q_values": None,
            },
            {
                "vendor_id": "GUDIMALKAPUR_POTATO_01",
                "location": {"status": "VENDOR_SPECIFIC_APPROXIMATE", "lat": 17.3871, "lon": 78.43911},
                "individual_price_rs_per_kg": 12,
                "practical_horizon_days": 3,
                "user_provided_q_i": 33,
                "diary_records": None,
                "peer_q_values": None,
            },
            {
                "vendor_id": "MEHDIPATNAM_POTATO_01",
                "location": {"status": "VENDOR_SPECIFIC_APPROXIMATE", "lat": 17.39508, "lon": 78.44113},
                "individual_price_rs_per_kg": 16,
                "practical_horizon_days": 3,
                "user_provided_q_i": 20,
                "diary_records": None,
                "peer_q_values": None,
            },
            {
                "vendor_id": "ERRAGADDA_POTATO_01",
                "location": {"status": "VENDOR_SPECIFIC_APPROXIMATE", "lat": 17.45164, "lon": 78.43521},
                "individual_price_rs_per_kg": 16,
                "practical_horizon_days": 3,
                "user_provided_q_i": 25,
                "diary_records": None,
                "peer_q_values": None,
            },
        ],
        "config": {"d_max_km": 12, "trader_margin": 0.1, "transport_tiers": [{"capacity_kg": 1000, "cost_rs": 1800}]},
    }

    run_input = build_run_input(ProcurementAnalysisRequest(**payload))
    result = ProcurementRunService().run(run_input)

    assert result.run_status == RunStatus.COMPLETED.value
    assert result.total_vendors_submitted == 4
    assert result.eligible_vendor_count == 4
    assert result.candidate_group_count == 11
    assert result.selected_group_count == 1
    assert result.final_selection.total_savings_rs == 3732.6000000000004
    assert set(result.final_selection.selected_results[0].vendor_ids) == {
        "BOWENPALLY_POTATO_01",
        "ERRAGADDA_POTATO_01",
        "GUDIMALKAPUR_POTATO_01",
        "MEHDIPATNAM_POTATO_01",
    }
    assert result.final_selection.selected_results[0].decision.decision_state == "BUY_TOGETHER"
