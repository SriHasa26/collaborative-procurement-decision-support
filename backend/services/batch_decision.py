"""
Thin orchestration only (Phase 6D). No mathematical or selection logic
lives here -- it is delegated entirely to decision_evaluation.py and
selection.py, which themselves delegate all procurement math to Phase
6A's unmodified decision_engine/decision_math.
"""

from backend.models.contracts import CommodityParams, ConfigParams, ProcurementContext
from backend.models.decision_contracts import FinalSelectionResult
from backend.models.group_formation_contracts import GroupFormationResult
from backend.services.decision_evaluation import evaluate_candidate_groups
from backend.services.selection import select_final_groups


def run_procurement_decision(
    formation_result: GroupFormationResult,
    commodity: CommodityParams,
    context: ProcurementContext,
    config: ConfigParams,
) -> FinalSelectionResult:
    """Phase 6C candidate groups -> Phase 6A per-candidate evaluation ->
    Phase 5E WAIT/EXPAND refinement -> Phase 2B overlap-resolved final
    selection. One call per procurement context."""
    evaluated = evaluate_candidate_groups(formation_result, commodity, context, config)
    return select_final_groups(evaluated)
