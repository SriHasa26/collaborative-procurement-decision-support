"""
Data contracts for Phase 6D's candidate-group decision evaluation and
final selection.

Reuses, does not duplicate, Phase 6A's GroupDecisionResult (backend/
models/contracts.py) -- that object, produced unmodified by
decision_engine.evaluate_group, is embedded here exactly as-is
(`decision` field) so Phase 6A's own base-definition finding is never
lost or overwritten. Phase 6D's refinement (Phase 5E Section 12) is
represented as ADDITIONAL fields alongside it, never as a mutation of it.
"""

from dataclasses import dataclass, field
from typing import Tuple

from backend.models.contracts import GroupDecisionResult


@dataclass(frozen=True)
class EvaluatedGroupResult:
    """One candidate group's full decision outcome.

    `decision` is Phase 6A's own, completely unmodified GroupDecisionResult
    -- the base-definition answer (Phase 5D Section 9) as evaluate_group
    computed it, preserved forever for traceability/audit.

    `final_decision_state` is Phase 6D's AUTHORITATIVE, post-refinement
    state:
      - identical to decision.decision_state for BUY_TOGETHER, ABSTAIN,
        and DO_NOT_BUY_TOGETHER base results (no refinement applies).
      - for a WAIT_OR_EXPAND_GROUP base result: remains
        WAIT_OR_EXPAND_GROUP if >=1 pool superset resolves it, or is
        downgraded to DO_NOT_BUY_TOGETHER if none does (Phase 5E Section
        12's termination rule).

    resolving_superset_group_ids is non-empty ONLY for a WAIT_OR_EXPAND_GROUP
    whose trigger was checked against the pool and found resolvable --
    listing the ALREADY-GENERATED (never dynamically created) superset
    candidate group_id(s) from the SAME source_pool_id that independently
    evaluated to BUY_TOGETHER.
    """
    decision: GroupDecisionResult
    final_decision_state: str  # DecisionState value
    commodity_id: str
    context_date: str
    source_pool_id: str
    pool_vendor_ids: Tuple[str, ...]
    vendor_ids: Tuple[str, ...]  # this candidate's own members, sorted
    resolving_superset_group_ids: Tuple[str, ...] = field(default_factory=tuple)
    expansion_reason: str = ""  # populated only when the WAIT/EXPAND refinement applied


@dataclass(frozen=True)
class FinalSelectionResult:
    """Batch-level outcome for one procurement context: which BUY_TOGETHER
    candidates were selected (overlap-resolved, lexicographic objective),
    and full traceability for every evaluated candidate, selected or not."""
    commodity_id: str
    context_date: str
    selected_group_ids: Tuple[str, ...]
    selected_results: Tuple[EvaluatedGroupResult, ...]
    non_selected_buy_together_results: Tuple[EvaluatedGroupResult, ...]
    wait_or_expand_results: Tuple[EvaluatedGroupResult, ...]
    do_not_buy_results: Tuple[EvaluatedGroupResult, ...]
    abstained_results: Tuple[EvaluatedGroupResult, ...]
    all_evaluated_results: Tuple[EvaluatedGroupResult, ...]
    total_savings_rs: float
    total_vendor_coverage: int
    tie_break_note: str = ""
