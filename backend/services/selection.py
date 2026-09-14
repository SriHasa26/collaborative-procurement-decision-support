"""
Overlap resolution and final group selection (Phase 6D Part 4-7).

Authoritative source: Phase 2B Part 11 (the lexicographic objective:
primary = maximize total net savings, secondary = maximize distinct
vendor coverage, tie-break only -- never a weighted composite); Phase 2B
Part 12 (mutual exclusivity: no vendor may appear in more than one
SELECTED group); Phase 2B Part 15 Step 6 (V1 default: exact brute-force
enumeration over combinations of non-overlapping feasible candidates).

FORMAL RULE (Phase 2B Part 11-12, restated exactly, not redefined):
    x_G in {0,1} for each BUY_TOGETHER candidate G
    for every vendor i: sum(x_G for G containing i) <= 1
    primary objective:   maximize sum(savings(G) * x_G)
    secondary objective: maximize |union of vendors in selected G|,
                          used ONLY to break exact ties on the primary
                          objective -- never combined into one number.

ONLY BUY_TOGETHER (post-WAIT/EXPAND-refinement) candidates are eligible
for selection -- ABSTAIN, DO_NOT_BUY_TOGETHER, and WAIT_OR_EXPAND_GROUP
results (whether resolved or unresolved) are never selectable, per Phase
6D Part 3's explicit instruction not to assume every non-ABSTAIN group is
selectable.

SCOPE (Phase 6D Part 5): exhaustive search over combinations of the
BUY_TOGETHER candidate pool, matching Phase 2B's own V1 default. This is
O(2^m) in the number of BUY_TOGETHER candidates -- appropriate at this
project's documented ~5-20 vendor scope (where m, the number of
candidates that SURVIVE all the way to BUY_TOGETHER, is expected to be
small), and explicitly NOT claimed to be an internet-scale optimization
method.
"""

import itertools
from typing import List, Sequence, Tuple

from backend.models.decision_contracts import EvaluatedGroupResult, FinalSelectionResult
from backend.models.enums import DecisionState


def _is_disjoint(results: Sequence[EvaluatedGroupResult]) -> bool:
    seen = set()
    for r in results:
        if seen & set(r.vendor_ids):
            return False
        seen |= set(r.vendor_ids)
    return True


def _select_best_combination(
    buy_together: Sequence[EvaluatedGroupResult],
) -> Tuple[List[EvaluatedGroupResult], str]:
    """Exact exhaustive search over all subsets of the BUY_TOGETHER
    candidate pool (including the empty selection, which is always a
    valid baseline). Lexicographic objective (Phase 2B Part 11):
        1. maximize total savings
        2. maximize distinct vendor coverage (tie-break only)
    A THIRD-level tie-break is used only if both are exactly equal --
    Phase 2B does not specify one, so this uses a neutral, documented,
    implementation-level rule (the lexicographically smallest sorted
    tuple of selected group_ids), per Phase 6D Part 4's explicit
    instruction not to invent a new mathematically meaningful criterion."""
    sorted_candidates = sorted(buy_together, key=lambda r: r.decision.group_id)
    n = len(sorted_candidates)

    best_key: Tuple[float, int] = (float("-inf"), -1)
    best_combos: List[Tuple[EvaluatedGroupResult, ...]] = []

    for size in range(0, n + 1):
        for combo in itertools.combinations(sorted_candidates, size):
            if not _is_disjoint(combo):
                continue
            total_savings = sum(r.decision.savings_rs for r in combo)
            covered = set()
            for r in combo:
                covered |= set(r.vendor_ids)
            key = (total_savings, len(covered))
            if key > best_key:
                best_key = key
                best_combos = [combo]
            elif key == best_key:
                best_combos.append(combo)

    chosen = min(best_combos, key=lambda combo: tuple(sorted(r.decision.group_id for r in combo)))

    if len(best_combos) > 1:
        tie_break_note = (
            f"Lexicographic objective (savings, then vendor coverage) produced "
            f"{len(best_combos)} tied optimal selections at savings=Rs {best_key[0]:.2f}, "
            f"coverage={best_key[1]} vendors. Resolved by the lexicographically "
            f"smallest sorted group-ID tuple -- a neutral, implementation-level "
            f"deterministic rule (Phase 2B does not specify a further criterion), "
            f"not a new optimization objective."
        )
    else:
        tie_break_note = "Unique optimum under the lexicographic objective -- no tie-break needed."

    return list(chosen), tie_break_note


def select_final_groups(evaluated_results: Sequence[EvaluatedGroupResult]) -> FinalSelectionResult:
    """Partitions all evaluated candidates by final_decision_state, runs
    exact overlap resolution over the BUY_TOGETHER subset only, and
    assembles the full, explainable batch result."""
    buy_together = [r for r in evaluated_results if r.final_decision_state == DecisionState.BUY_TOGETHER.value]
    wait_or_expand = [r for r in evaluated_results if r.final_decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value]
    do_not_buy = [r for r in evaluated_results if r.final_decision_state == DecisionState.DO_NOT_BUY_TOGETHER.value]
    abstained = [r for r in evaluated_results if r.final_decision_state == DecisionState.ABSTAIN.value]

    selected, tie_break_note = _select_best_combination(buy_together)
    selected_ids = tuple(sorted(r.decision.group_id for r in selected))

    non_selected_buy_together = [r for r in buy_together if r.decision.group_id not in selected_ids]

    total_savings = sum(r.decision.savings_rs for r in selected)
    covered_vendors = set()
    for r in selected:
        covered_vendors |= set(r.vendor_ids)

    commodity_id = evaluated_results[0].commodity_id if evaluated_results else ""
    context_date = evaluated_results[0].context_date if evaluated_results else ""

    return FinalSelectionResult(
        commodity_id=commodity_id,
        context_date=context_date,
        selected_group_ids=selected_ids,
        selected_results=tuple(selected),
        non_selected_buy_together_results=tuple(sorted(non_selected_buy_together, key=lambda r: r.decision.group_id)),
        wait_or_expand_results=tuple(sorted(wait_or_expand, key=lambda r: r.decision.group_id)),
        do_not_buy_results=tuple(sorted(do_not_buy, key=lambda r: r.decision.group_id)),
        abstained_results=tuple(sorted(abstained, key=lambda r: r.decision.group_id)),
        all_evaluated_results=tuple(evaluated_results),
        total_savings_rs=total_savings,
        total_vendor_coverage=len(covered_vendors),
        tie_break_note=tie_break_note,
    )


def explain(result: EvaluatedGroupResult, selection: "FinalSelectionResult | None" = None) -> str:
    """Produces the human-readable explanation for one evaluated result,
    reflecting only actual computed fields -- nothing fabricated (Phase
    6D Part 7)."""
    state = result.final_decision_state

    if state == DecisionState.BUY_TOGETHER.value:
        if selection is not None and result.decision.group_id not in selection.selected_group_ids:
            return (
                f"Group {result.decision.group_id} was feasible (BUY_TOGETHER, savings "
                f"Rs {result.decision.savings_rs:.2f}) but not selected because it "
                f"overlapped with a lexicographically better solution "
                f"(selected groups: {', '.join(selection.selected_group_ids) or 'none'})."
            )
        return (
            f"Group satisfies geographic, demand, freshness, MOQ and economic "
            f"requirements. {result.decision.reason}"
        )

    if state == DecisionState.WAIT_OR_EXPAND_GROUP.value:
        return result.expansion_reason or result.decision.reason

    if state == DecisionState.ABSTAIN.value:
        return f"Insufficient evidence: {result.decision.reason}"

    if state == DecisionState.DO_NOT_BUY_TOGETHER.value:
        base = "Group was evaluable but collaborative procurement was not justified under the defined constraints."
        if result.expansion_reason:
            return f"{base} {result.expansion_reason}"
        return f"{base} {result.decision.reason}"

    return result.decision.reason
