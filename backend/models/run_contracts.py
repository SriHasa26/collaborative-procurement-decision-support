"""
Run-level data contracts for Phase 6E's application-level orchestration
layer.

Phase 6E owns none of the underlying rules (validation, demand estimation,
eligibility, geographic compatibility, group formation, candidate
evaluation, WAIT/EXPAND resolution, overlap resolution, selection) -- all
of that remains Phase 6A/6B/6C/6D's authoritative territory. These
contracts exist ONLY to carry one run's INPUT and to assemble one run's
COMPLETE, already-computed OUTPUT for inspection, without duplicating any
field those phases already define.

ProcurementRunInput reuses Phase 6A's CommodityParams/ProcurementContext/
ConfigParams and Phase 6B's VendorSubmission verbatim -- no second vendor
schema is introduced.

ProcurementRunResult embeds, rather than flattens or re-derives,
Phase 6B's BatchEligibilityResult, Phase 6C's GroupFormationResult, and
Phase 6D's FinalSelectionResult exactly as those phases produced them --
this is the same "wrap, never mutate or duplicate" pattern Phase 6D itself
used for Phase 6A's GroupDecisionResult (see backend/models/
decision_contracts.py's own docstring). The only NEW information here is
the run-level status and a handful of plain integer counts, each one
computed once (in backend/services/procurement_run.py) directly from the
lengths of the embedded collections -- never independently fabricated.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from backend.models.batch_contracts import BatchEligibilityResult, VendorSubmission
from backend.models.contracts import CommodityParams, ConfigParams, ProcurementContext
from backend.models.decision_contracts import FinalSelectionResult
from backend.models.group_formation_contracts import GroupFormationResult


class RunStatus(str, Enum):
    """Run-level outcome status -- a NEW, Phase 6E-owned concept, distinct
    from (and never a substitute for) vendor-level OutcomeKind (OK/ABSTAIN/
    VALIDATION_ERROR) or group-level DecisionState (BUY_TOGETHER/etc.).
    A run can legitimately be COMPLETED even when individual vendors
    abstained or groups were rejected -- these are different concepts and
    must never be merged (Phase 6E Section 8's explicit instruction).

    Assigned by backend.services.procurement_run.ProcurementRunService.run
    using the precedence order documented there (earliest-applicable
    pipeline-stage outcome wins) -- see that module's docstring for the
    exact precedence table. Every status is a direct, derived consequence
    of the pipeline's own actual output; none is fabricated.
    """
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ABSTENTIONS = "COMPLETED_WITH_ABSTENTIONS"
    COMPLETED_NO_SELECTION = "COMPLETED_NO_SELECTION"
    COMPLETED_NO_GROUPS = "COMPLETED_NO_GROUPS"
    COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS = "COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS"
    COMPLETED_INVALID_CONTEXT = "COMPLETED_INVALID_CONTEXT"


@dataclass(frozen=True)
class ProcurementRunInput:
    """Everything needed for exactly one procurement analysis run:
    (commodity, time/context, vendor universe) -- Phase 5E's own definition
    of one run's scope, restated, not redefined. `config` carries d_max_km
    (needed by Phase 6C group formation) together with the trader margin
    and transport tiers (needed by Phase 6D decision evaluation) -- reusing
    Phase 6A's existing ConfigParams rather than splitting it into two
    partially-overlapping new shapes."""
    commodity: CommodityParams
    context: ProcurementContext
    vendor_submissions: Tuple[VendorSubmission, ...]
    config: ConfigParams


@dataclass(frozen=True)
class ProcurementRunResult:
    """The complete, inspectable outcome of one procurement run.

    `group_formation` is None only when group formation was never
    attempted (Phase 6E pipeline Steps 5): an invalid context or fewer
    than 2 eligible vendors. `final_selection` is None whenever
    `group_formation` is None, AND also when group formation ran but
    produced zero candidate groups (Step 7) -- in both cases, running
    Phase 6D's evaluation/selection over an empty or absent input would
    be meaningless, not merely redundant.

    Every *_count field is a plain `len()` of the corresponding embedded
    collection below, computed once at assembly time -- never an
    independently-tracked or estimated number."""
    run_status: str  # RunStatus value
    commodity_id: str
    context_date: str
    total_vendors_submitted: int
    eligible_vendor_count: int
    abstained_vendor_count: int
    validation_error_vendor_count: int
    candidate_group_count: int
    selected_group_count: int
    batch_eligibility: BatchEligibilityResult
    group_formation: Optional[GroupFormationResult] = None
    final_selection: Optional[FinalSelectionResult] = None
