"""
Phase 6D tests: overlap resolution and lexicographic final selection
(backend/services/selection.py).

Covers required test cases T8-T14 (numbering per the Phase 6D task spec):
  T8  -- simple overlap (two BUY_TOGETHER candidates share a vendor)
  T9  -- savings priority over coverage (primary objective wins outright)
  T10 -- coverage tie-break (equal savings, differing coverage)
  T11 -- non-overlapping groups: both selected
  T12 -- ABSTAIN exclusion from optimization
  T13 -- WAIT_OR_EXPAND_GROUP exclusion from selection
  T14 -- determinism across repeated runs (selection layer)

Plus one additional (not separately numbered) test exercising the neutral,
documented third-level tie-break for when savings AND coverage both tie
exactly -- Part 4's "no third-level criterion" fallback path, otherwise
left completely untested.

All EvaluatedGroupResult inputs are hand-built via
tests/fixtures/decision_selection_fixtures.make_*() helpers -- selection.py
only ever reads .decision.group_id, .decision.savings_rs, .vendor_ids, and
.final_decision_state, so these minimal fixtures are a faithful test of
this layer's actual contract without re-deriving new economics.
"""

from backend.services.selection import explain, select_final_groups
from tests.fixtures.decision_selection_fixtures import (
    make_abstain,
    make_buy_together,
    make_do_not_buy,
    make_wait_or_expand,
)


# --- T8: simple overlap ---
def test_t8_simple_overlap_picks_higher_savings():
    x = make_buy_together("X", savings_rs=100.0, vendor_ids=("A", "B"))
    y = make_buy_together("Y", savings_rs=90.0, vendor_ids=("B", "C"))  # overlaps X on B

    result = select_final_groups([x, y])

    assert result.selected_group_ids == ("X",)
    assert result.total_savings_rs == 100.0
    assert result.total_vendor_coverage == 2
    non_selected_ids = {r.decision.group_id for r in result.non_selected_buy_together_results}
    assert non_selected_ids == {"Y"}


# --- T9: savings priority over coverage (mutually-exclusive alternatives) ---
def test_t9_savings_priority_over_coverage():
    g_savings = make_buy_together("G_savings", savings_rs=150.0, vendor_ids=("A", "B"))
    g_coverage = make_buy_together("G_coverage", savings_rs=140.0, vendor_ids=("A", "C", "D"))  # overlaps on A

    result = select_final_groups([g_savings, g_coverage])

    # G_coverage covers more vendors (3 vs 2) but has lower total savings --
    # the primary objective (savings) must win outright, never combined
    # with coverage into one weighted number.
    assert result.selected_group_ids == ("G_savings",)
    assert result.total_savings_rs == 150.0
    assert result.total_vendor_coverage == 2


# --- T10: coverage tie-break (equal savings, mutually-exclusive alternatives) ---
def test_t10_coverage_tie_break_when_savings_are_equal():
    g_wide = make_buy_together("G_wide", savings_rs=100.0, vendor_ids=("A", "B", "C"))
    g_narrow = make_buy_together("G_narrow", savings_rs=100.0, vendor_ids=("A", "B"))  # overlaps on A, B

    result = select_final_groups([g_wide, g_narrow])

    # Exact tie on the PRIMARY objective (savings=100 either way) -- the
    # SECONDARY objective (vendor coverage) breaks the tie: 3 > 2.
    assert result.selected_group_ids == ("G_wide",)
    assert result.total_savings_rs == 100.0
    assert result.total_vendor_coverage == 3
    assert result.tie_break_note == "Unique optimum under the lexicographic objective -- no tie-break needed."


# --- T11: non-overlapping groups: both selected ---
def test_t11_non_overlapping_groups_both_selected():
    g1 = make_buy_together("G1", savings_rs=50.0, vendor_ids=("A", "B"))
    g2 = make_buy_together("G2", savings_rs=60.0, vendor_ids=("C", "D"))

    result = select_final_groups([g1, g2])

    assert result.selected_group_ids == ("G1", "G2")
    assert result.total_savings_rs == 110.0
    assert result.total_vendor_coverage == 4
    assert result.non_selected_buy_together_results == ()


# --- T12: ABSTAIN exclusion from optimization ---
def test_t12_abstain_excluded_from_optimization():
    buy = make_buy_together("G1", savings_rs=50.0, vendor_ids=("A", "B"))
    abstained = make_abstain("G_abstain", vendor_ids=("C", "D"))

    result = select_final_groups([buy, abstained])

    assert result.selected_group_ids == ("G1",)
    assert result.total_savings_rs == 50.0
    assert result.total_vendor_coverage == 2  # C, D never counted
    abstained_ids = {r.decision.group_id for r in result.abstained_results}
    assert abstained_ids == {"G_abstain"}


# --- T13: WAIT_OR_EXPAND_GROUP exclusion from selection ---
def test_t13_wait_or_expand_excluded_from_selection_even_with_high_savings():
    buy = make_buy_together("G1", savings_rs=50.0, vendor_ids=("A", "B"))
    # Deliberately higher hypothetical savings than the BUY_TOGETHER
    # candidate, to prove exclusion is by STATE, never by comparing numbers.
    waiting = make_wait_or_expand("G_wait", savings_rs=9999.0, vendor_ids=("C", "D"))

    result = select_final_groups([buy, waiting])

    assert result.selected_group_ids == ("G1",)
    assert result.total_savings_rs == 50.0  # the 9999 figure never enters the total
    assert result.total_vendor_coverage == 2
    waiting_ids = {r.decision.group_id for r in result.wait_or_expand_results}
    assert waiting_ids == {"G_wait"}


# --- T14: determinism across repeated runs (selection layer) ---
def test_t14_selection_is_deterministic_across_repeated_runs():
    inputs = [
        make_buy_together("G1", savings_rs=50.0, vendor_ids=("A", "B")),
        make_buy_together("G2", savings_rs=60.0, vendor_ids=("C", "D")),
        make_buy_together("G3", savings_rs=40.0, vendor_ids=("B", "E")),  # overlaps G1
        make_wait_or_expand("G_wait", savings_rs=500.0, vendor_ids=("F", "G")),
        make_do_not_buy("G_no", vendor_ids=("H", "I")),
        make_abstain("G_abstain", vendor_ids=("J", "K")),
    ]

    first = select_final_groups(list(inputs))
    second = select_final_groups(list(inputs))

    assert first.selected_group_ids == second.selected_group_ids
    assert first.total_savings_rs == second.total_savings_rs
    assert first.total_vendor_coverage == second.total_vendor_coverage
    assert first.tie_break_note == second.tie_break_note


# --- Additional: neutral third-level tie-break when savings AND coverage
# both tie exactly across multiple mutually-exclusive optimal combinations
# (Phase 2B specifies no third-level criterion -- Part 4's documented,
# non-mathematical fallback: smallest sorted group-ID tuple). ---
def test_third_level_neutral_tie_break_on_exact_double_tie():
    # {G_pair} alone: savings=100, coverage=2.
    # {G_alt} alone: savings=100, coverage=2 (same key exactly), overlaps G_pair on A.
    g_pair = make_buy_together("G_pair", savings_rs=100.0, vendor_ids=("A", "B"))
    g_alt = make_buy_together("G_alt", savings_rs=100.0, vendor_ids=("A", "C"))

    result = select_final_groups([g_pair, g_alt])

    # Both single-group combos tie at (savings=100, coverage=2) exactly;
    # the deterministic fallback picks the lexicographically smallest
    # sorted group-ID tuple: ("G_alt",) < ("G_pair",).
    assert result.selected_group_ids == ("G_alt",)
    assert "tied" in result.tie_break_note
    assert "neutral" in result.tie_break_note


# --- explain(): reflects only actual computed fields ---
def test_explain_buy_together_selected_vs_non_selected():
    x = make_buy_together("X", savings_rs=100.0, vendor_ids=("A", "B"))
    y = make_buy_together("Y", savings_rs=90.0, vendor_ids=("B", "C"))
    result = select_final_groups([x, y])

    selected_explanation = explain(x, result)
    non_selected_explanation = explain(y, result)

    assert "satisfies" in selected_explanation.lower()
    assert "not selected" in non_selected_explanation
    assert "X" in non_selected_explanation  # names the selected alternative it lost to


def test_explain_abstain_and_do_not_buy_together():
    abstained = make_abstain("G_abstain", vendor_ids=("A", "B"))
    do_not_buy = make_do_not_buy("G_no", vendor_ids=("C", "D"))

    assert explain(abstained).startswith("Insufficient evidence:")
    assert "not justified" in explain(do_not_buy)
