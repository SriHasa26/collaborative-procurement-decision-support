"""
Phase 6D tests: candidate-group decision evaluation and WAIT_OR_EXPAND_GROUP
superset resolution (backend/services/decision_evaluation.py).

Covers required test cases T1-T7 (numbering per the Phase 6D task spec):
  T1 -- BUY_TOGETHER candidate evaluation
  T2 -- DO_NOT_BUY_TOGETHER candidate evaluation
  T3 -- ABSTAIN candidate evaluation
  T4 -- WAIT_OR_EXPAND_GROUP base decision, BEFORE resolution
  T5 -- successful superset expansion (same pool)
  T6 -- unsuccessful superset expansion / termination (no superset in pool)
  T7 -- different pools -- no cross-pool expansion

Reuses Phase 5E Section 15's own worked example (imported from
tests/fixtures/decision_selection_fixtures.py, itself importing V1-V7 from
tests/fixtures/group_formation_fixtures.py) wherever that scenario's
existing structure already exercises the case -- no new economics are
invented for T1-T6.
"""

import pytest

from backend.models.enums import DecisionState
from backend.models.group_formation_contracts import GroupFormationResult
from backend.services.decision_evaluation import evaluate_candidate_groups, resolve_wait_or_expand
from tests.fixtures.decision_selection_fixtures import (
    COMMODITY,
    COMMODITY_ID,
    CONFIG,
    CONTEXT,
    CONTEXT_DATE,
    FULL_POOL_RECORDS,
    RECORD_T2_DO_NOT_BUY,
    RECORD_T3_ABSTAIN,
    RECORD_T6_NO_SUPERSET,
    make_buy_together,
    make_wait_or_expand,
)


def _formation_result(records):
    return GroupFormationResult(
        commodity_id=COMMODITY_ID,
        context_date=CONTEXT_DATE,
        pools=(),
        candidate_groups=tuple(records),
        singleton_vendor_ids=(),
    )


def _by_group_id(results, group_id):
    matches = [r for r in results if r.decision.group_id == group_id]
    assert len(matches) == 1, f"expected exactly one result for {group_id}, found {len(matches)}"
    return matches[0]


# --- T1: BUY_TOGETHER ---
def test_t1_buy_together_candidate_evaluation():
    results = evaluate_candidate_groups(_formation_result(FULL_POOL_RECORDS), COMMODITY, CONTEXT, CONFIG)
    g_all = _by_group_id(results, "G_all")
    assert g_all.decision.decision_state == DecisionState.BUY_TOGETHER.value
    assert g_all.final_decision_state == DecisionState.BUY_TOGETHER.value
    assert g_all.decision.savings_rs == pytest.approx(1840.0)
    assert g_all.decision.moq_met is True
    assert g_all.resolving_superset_group_ids == ()


# --- T2: DO_NOT_BUY_TOGETHER ---
def test_t2_do_not_buy_together_candidate_evaluation():
    results = evaluate_candidate_groups(_formation_result([RECORD_T2_DO_NOT_BUY]), COMMODITY, CONTEXT, CONFIG)
    g4 = _by_group_id(results, "G4")
    assert g4.decision.decision_state == DecisionState.DO_NOT_BUY_TOGETHER.value
    assert g4.final_decision_state == DecisionState.DO_NOT_BUY_TOGETHER.value
    assert g4.decision.savings_rs == pytest.approx(-45.0)
    assert g4.resolving_superset_group_ids == ()
    assert g4.expansion_reason == ""  # no refinement applies -- base decision already final


# --- T3: ABSTAIN ---
def test_t3_abstain_candidate_evaluation():
    results = evaluate_candidate_groups(_formation_result([RECORD_T3_ABSTAIN]), COMMODITY, CONTEXT, CONFIG)
    g_abstain = _by_group_id(results, "G_abstain")
    assert g_abstain.decision.decision_state == DecisionState.ABSTAIN.value
    assert g_abstain.final_decision_state == DecisionState.ABSTAIN.value
    assert "ABSTAIN_V" in g_abstain.decision.reason
    assert "demand estimate" in g_abstain.decision.reason


# --- T4: WAIT_OR_EXPAND_GROUP base decision, BEFORE resolution ---
def test_t4_wait_or_expand_group_base_decision_before_resolution():
    results = evaluate_candidate_groups(_formation_result(FULL_POOL_RECORDS), COMMODITY, CONTEXT, CONFIG)
    g1 = _by_group_id(results, "G1")
    # The embedded Phase 6A GroupDecisionResult is Phase 5D's own
    # base-definition answer and must never be mutated by Phase 6D's
    # refinement, regardless of what final_decision_state becomes.
    assert g1.decision.decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value
    assert g1.decision.savings_rs == pytest.approx(1550.0)
    assert g1.decision.moq_shortfall_kg == pytest.approx(20.0)


# --- T5: successful superset expansion (same pool) ---
def test_t5_successful_superset_expansion_same_pool():
    results = evaluate_candidate_groups(_formation_result(FULL_POOL_RECORDS), COMMODITY, CONTEXT, CONFIG)
    for wait_group_id in ("G1", "G2", "G3"):
        g = _by_group_id(results, wait_group_id)
        # Base decision (Phase 5D) is untouched...
        assert g.decision.decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value
        # ...but the FINAL, authoritative state remains WAIT_OR_EXPAND_GROUP --
        # it is NEVER silently upgraded to BUY_TOGETHER, even though a
        # resolving superset was found (Phase 6D Part 2 Step 8).
        assert g.final_decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value
        assert g.resolving_superset_group_ids == ("G_all",)
        assert "G_all" in g.expansion_reason

    # G_all itself is unaffected (its own base decision was already BUY_TOGETHER).
    g_all = _by_group_id(results, "G_all")
    assert g_all.final_decision_state == DecisionState.BUY_TOGETHER.value
    assert g_all.resolving_superset_group_ids == ()


# --- T6: unsuccessful superset expansion / termination (no superset exists) ---
def test_t6_unsuccessful_expansion_terminates_to_do_not_buy_together():
    results = evaluate_candidate_groups(_formation_result([RECORD_T6_NO_SUPERSET]), COMMODITY, CONTEXT, CONFIG)
    g3 = _by_group_id(results, "G3")
    # Base decision (Phase 5D) still shows the honest WAIT trigger...
    assert g3.decision.decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value
    # ...but since the pool (V3, V4) contains no larger candidate at all,
    # Phase 5E Section 12's termination rule applies: DOWNGRADE, not an
    # open-ended wait.
    assert g3.final_decision_state == DecisionState.DO_NOT_BUY_TOGETHER.value
    assert g3.resolving_superset_group_ids == ()
    assert "no already-generated larger group" in g3.expansion_reason


# --- T7: different pools -- no cross-pool expansion ---
def test_t7_no_cross_pool_expansion():
    # W is WAIT_OR_EXPAND_GROUP in POOL_X; S is a real vendor-set superset
    # of W (by vendor_ids) and evaluates to BUY_TOGETHER, but lives in a
    # DIFFERENT pool (POOL_Y). The superset search must never cross pools,
    # even when a resolving-looking candidate exists elsewhere.
    w = make_wait_or_expand("W", savings_rs=500.0, vendor_ids=("A", "B"), pool_id="POOL_X")
    s = make_buy_together("S", savings_rs=1000.0, vendor_ids=("A", "B", "C"), pool_id="POOL_Y")

    refined = resolve_wait_or_expand([w, s])
    refined_w = _by_group_id(refined, "W")
    refined_s = _by_group_id(refined, "S")

    assert refined_w.final_decision_state == DecisionState.DO_NOT_BUY_TOGETHER.value
    assert refined_w.resolving_superset_group_ids == ()
    # S itself passes through completely unchanged (no refinement applies to it).
    assert refined_s.final_decision_state == DecisionState.BUY_TOGETHER.value
    assert refined_s.resolving_superset_group_ids == ()


def test_resolve_wait_or_expand_does_not_mutate_input_objects():
    w = make_wait_or_expand("W2", savings_rs=200.0, vendor_ids=("A", "B"), pool_id="POOL_Z")
    original_final_state = w.final_decision_state
    resolve_wait_or_expand([w])
    assert w.final_decision_state == original_final_state  # unchanged -- dataclasses.replace() only
