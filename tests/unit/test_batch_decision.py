"""
Phase 6D integration test: the full pipeline from Phase 6C's real
form_candidate_groups through Phase 6D's evaluate_candidate_groups and
select_final_groups (backend/services/batch_decision.run_procurement_decision).

Unlike test_decision_evaluation.py and test_selection.py (which use a
hand-picked subset of candidates, or hand-built results, to isolate one
mechanism at a time), this file runs the REAL, complete candidate
enumeration (all 2^5 - 5 - 1 = 26 subsets of Phase 5E Section 15's 5-vendor
pool) through the entire Phase 6C -> 6D pipeline, to confirm the pieces
integrate correctly end-to-end. It deliberately does NOT assert on every
one of the 26 candidates' outcomes (only the 5 already regression-tested
in tests/unit/test_decision_engine_regression.py and
tests/unit/test_decision_evaluation.py), since this project's rule against
fabricating results applies to test assertions too: no claim is made here
about a candidate's outcome that was not actually verified.

Also covers T14 (determinism) at the full-pipeline level.
"""

from backend.services.batch_decision import run_procurement_decision
from backend.services.group_formation import form_candidate_groups
from tests.fixtures.decision_selection_fixtures import COMMODITY, CONFIG, CONTEXT, COMMODITY_ID, CONTEXT_DATE
from tests.fixtures.group_formation_fixtures import V1, V2, V3, V4, V7


def _form_full_pool():
    return form_candidate_groups(
        eligible_vendors=[V1, V2, V3, V4, V7],
        commodity_id=COMMODITY_ID,
        context_date=CONTEXT_DATE,
        d_max_km=CONFIG.d_max_km,
    )


def _by_group_id(all_evaluated, group_id):
    matches = [r for r in all_evaluated if r.decision.group_id == group_id]
    assert len(matches) == 1, f"expected exactly one result for {group_id}, found {len(matches)}"
    return matches[0]


def test_full_pipeline_reproduces_known_regression_outcomes():
    formation = _form_full_pool()
    # Sanity check: exactly the pool Phase 6C's own formula predicts
    # (2^5 - 5 - 1 = 26), and all 5 vendors form one connected pool.
    assert len(formation.candidate_groups) == 26
    assert len(formation.pools) == 1
    assert formation.singleton_vendor_ids == ()

    result = run_procurement_decision(formation, COMMODITY, CONTEXT, CONFIG)
    all_evaluated = result.all_evaluated_results

    g_all = _by_group_id(all_evaluated, "V1+V2+V3+V4+V7")
    assert g_all.decision.decision_state == "BUY_TOGETHER"
    assert g_all.decision.savings_rs == 1840.0

    g4 = _by_group_id(all_evaluated, "V3+V7")
    assert g4.decision.decision_state == "DO_NOT_BUY_TOGETHER"
    assert g4.decision.savings_rs == -45.0

    for wait_group_id in ("V1+V2+V3+V4", "V1+V2+V7", "V3+V4"):
        g = _by_group_id(all_evaluated, wait_group_id)
        assert g.decision.decision_state == "WAIT_OR_EXPAND_GROUP"
        # The full 5-vendor group is a real, already-generated superset of
        # each of these -- it must appear among the resolving supersets,
        # even if other same-pool supersets also happen to qualify.
        assert "V1+V2+V3+V4+V7" in g.resolving_superset_group_ids
        assert g.final_decision_state == "WAIT_OR_EXPAND_GROUP"

    # The full group alone already achieves Rs 1840 savings; the exhaustive
    # overlap-resolved search can never select a combination worth less
    # than the best single candidate it considered.
    assert result.total_savings_rs >= 1840.0

    # Mutual-exclusivity invariant: no vendor appears in more than one
    # selected group.
    seen_vendors = set()
    for r in result.selected_results:
        assert not (seen_vendors & set(r.vendor_ids))
        seen_vendors |= set(r.vendor_ids)


def test_t14_full_pipeline_determinism_across_repeated_runs():
    formation = _form_full_pool()

    first = run_procurement_decision(formation, COMMODITY, CONTEXT, CONFIG)
    second = run_procurement_decision(formation, COMMODITY, CONTEXT, CONFIG)

    assert first.selected_group_ids == second.selected_group_ids
    assert first.total_savings_rs == second.total_savings_rs
    assert first.total_vendor_coverage == second.total_vendor_coverage
    assert [r.decision.group_id for r in first.all_evaluated_results] == \
           [r.decision.group_id for r in second.all_evaluated_results]
