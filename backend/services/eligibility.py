"""
Per-vendor eligibility evaluation.

Scope discipline (Phase 6B Step 15): this module does NOT calculate
pairwise geographic compatibility, does NOT build a graph, does NOT
select groups. It determines exactly one thing per vendor: is there
enough valid, non-fabricated evidence for this vendor to proceed to
Phase 6C's group formation?

Reuses, does not duplicate (Phase 6B Step 1/4):
  - backend.services.demand_estimation.estimate_demand / ValidationError
    (Phase 6A, unchanged) for diary/peer-based demand resolution.
  - backend.models.contracts.VendorInput / TaggedLocation (Phase 6A,
    unchanged) as the eligible-vendor output shape.

Evaluation order (Phase 6B Step 6), fixed and explicit:
  1. Structural validation (validation.validate_vendor_structure)
  2. Resolve/estimate demand (direct value, else Phase 6A's hierarchy)
  3. Validate the demand result (ABSTAIN if insufficient evidence)
  4. Check location availability
  5. Check horizon availability
  6. Determine eligibility

DOCUMENTED AMBIGUITY (Phase 6B Step 13 -- not silently decided): Phase
5C/5D's demand hierarchy discusses "history" (diary records) versus
"same-category peers" (cold-start), but does not explicitly rank a
one-time, directly user-stated quantity (Phase 1C's original survey
"typical daily consumption" question) against diary-derived estimates.
This implementation makes an explicit, documented choice: a directly
user-provided q_i takes precedence over diary/peer estimation, on the
grounds that Phase 1C's original design treated the survey-stated figure
as the Priority-1 primary economic baseline, with diary/cold-start as
supplementary/fallback instruments (Phase 1C Section 3, C2). This is
stated as a reasoned interpretation, not an asserted authoritative rule,
since no prior phase explicitly ranked these two relative to each other.

DOCUMENTED SCOPE BOUNDARY: individual_price_rs_per_kg is required by
Phase 6A's VendorInput/evaluate_group, but is NOT named among Phase 5E
Section 4's three authoritative eligibility fields (q_i, L_i, H_i,c), nor
in this phase's own Step 5 field list. This implementation therefore does
NOT treat a missing individual price as an eligibility failure -- an
eligible VendorInput may carry individual_price_rs_per_kg=None, and Phase
6A's evaluate_group will correctly ABSTAIN on it later if a group
containing this vendor is ever evaluated. This is a deliberate,
documented scope decision, not an oversight -- see
reports/phase6b_validation_and_eligibility_report.md, Section 8.
"""

from backend.models.batch_contracts import VendorEligibilityResult, VendorSubmission
from backend.models.contracts import ProcurementContext, VendorInput
from backend.models.enums import EstimationProvenance, OutcomeKind
from backend.models.reasons import AbstentionReason, ValidationErrorReason
from backend.services import validation
from backend.services.demand_estimation import EstimationResult, ValidationError, estimate_demand


def _resolve_demand(submission: VendorSubmission) -> EstimationResult:
    """Direct user-provided value takes precedence; else defer entirely
    to Phase 6A's estimate_demand (unmodified). See module docstring for
    the documented precedence ambiguity."""
    if submission.user_provided_q_i is not None:
        return EstimationResult(
            outcome=OutcomeKind.OK,
            q_i=submission.user_provided_q_i,
            provenance=EstimationProvenance.USER_PROVIDED,
            reason="directly user-provided quantity (survey-stated).",
        )
    return estimate_demand(submission.diary_records, submission.peer_q_values)


def evaluate_vendor(submission: VendorSubmission, context: ProcurementContext) -> VendorEligibilityResult:
    """Evaluate one vendor independently. Never raises -- any exception
    from a reused Phase 6A function is caught here and converted into a
    structured VALIDATION_ERROR result, so one vendor's malformed input
    can never propagate into an unhandled exception that would affect
    batch processing of other vendors (Phase 6B's core design principle)."""

    # --- 1. Structural validation ---
    structural_error = validation.validate_vendor_structure(submission)
    if structural_error is not None:
        return VendorEligibilityResult(
            vendor_id=submission.vendor_id,
            status=OutcomeKind.VALIDATION_ERROR.value,
            eligible=False,
            vendor_input=None,
            demand_provenance=None,
            reason_code=structural_error,
            reason_detail=f"structural validation failed: {structural_error}",
        )

    # --- 2 & 3. Resolve demand, catching Phase 6A's ValidationError explicitly ---
    try:
        demand_result = _resolve_demand(submission)
    except ValidationError as exc:
        return VendorEligibilityResult(
            vendor_id=submission.vendor_id,
            status=OutcomeKind.VALIDATION_ERROR.value,
            eligible=False,
            vendor_input=None,
            demand_provenance=None,
            reason_code=ValidationErrorReason.NEGATIVE_QUANTITY.value,
            reason_detail=str(exc),
        )

    if demand_result.outcome == OutcomeKind.ABSTAIN:
        return VendorEligibilityResult(
            vendor_id=submission.vendor_id,
            status=OutcomeKind.ABSTAIN.value,
            eligible=False,
            vendor_input=None,
            demand_provenance=None,
            reason_code=AbstentionReason.INSUFFICIENT_DEMAND_EVIDENCE.value,
            reason_detail=demand_result.reason,
        )

    # --- 4. Location availability (authoritative field L_i, Phase 5E Section 4) ---
    if not submission.location.is_usable():
        return VendorEligibilityResult(
            vendor_id=submission.vendor_id,
            status=OutcomeKind.ABSTAIN.value,
            eligible=False,
            vendor_input=None,
            demand_provenance=demand_result.provenance,
            reason_code=AbstentionReason.MISSING_LOCATION.value,
            reason_detail=f"location status is {submission.location.status.value} -- not usable for geographic evaluation.",
        )

    # --- 5. Horizon availability (authoritative field H_i,c, Phase 5E Section 4) ---
    if submission.practical_horizon_days is None:
        return VendorEligibilityResult(
            vendor_id=submission.vendor_id,
            status=OutcomeKind.ABSTAIN.value,
            eligible=False,
            vendor_input=None,
            demand_provenance=demand_result.provenance,
            reason_code=AbstentionReason.MISSING_HORIZON.value,
            reason_detail="practical procurement horizon (H_i,c) is unavailable, directly or via proxy.",
        )

    # --- 6. Eligible: construct the Phase 6A VendorInput unchanged ---
    vendor_input = VendorInput(
        vendor_id=submission.vendor_id,
        location=submission.location,
        q_i=demand_result.q_i,
        estimation_provenance=demand_result.provenance,
        individual_price_rs_per_kg=submission.individual_price_rs_per_kg,
        practical_horizon_days=submission.practical_horizon_days,
    )
    return VendorEligibilityResult(
        vendor_id=submission.vendor_id,
        status=OutcomeKind.OK.value,
        eligible=True,
        vendor_input=vendor_input,
        demand_provenance=demand_result.provenance,
        reason_code=None,
        reason_detail="eligible -- all critical fields present.",
    )
