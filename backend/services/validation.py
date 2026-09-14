"""
Structural validation -- procurement context AND vendor-level checks.

Scope discipline (Phase 6B Step 15): this module performs NO cost/savings
calculation, NO group formation, NO demand estimation. It only checks that
submitted data is well-formed. Whether well-formed-but-empty data is
sufficient for a decision (ABSTAIN) is eligibility.py's job, not this
module's.

Vendor-level numeric-list validation (diary_records, peer_q_values) is
NOT duplicated here -- it is already implemented in Phase 6A's
backend/services/demand_estimation.py (_validate_numeric_records, raising
ValidationError) and is reused as-is by eligibility.py. This module only
adds the checks Phase 6A never needed: location structure, a single
directly-submitted q_i value, individual price, and practical horizon
(Phase 6B Step 3A).
"""

from typing import Optional

from backend.models.batch_contracts import ContextValidationResult, VendorSubmission
from backend.models.contracts import ProcurementContext
from backend.models.enums import VendorLocationStatus
from backend.models.reasons import ContextValidationReason, ValidationErrorReason


def validate_context(context: ProcurementContext, vendor_submissions) -> ContextValidationResult:
    """Structural validation of the procurement context and its vendor
    collection, per Phase 6B Step 2. Checks only fields the authoritative
    contracts actually require -- no new mandatory field is invented.

    NOTE ON SCOPE (documented, not silently decided): Phase 6B's task
    description names 'invalid procurement horizon if the horizon is
    required' as a possible context-level check. Phase 5D/5E's
    ProcurementContext contract (Phase 6A, backend/models/contracts.py)
    has NO horizon field at the context level -- the order horizon k is a
    per-GROUP decision variable computed in Stage 2 (Phase 5D Section 6),
    not a context input. This check therefore does not apply and is not
    implemented, rather than inventing a context-level horizon field that
    does not exist in the authoritative design.

    NOTE ON SCOPE (2): a missing wholesale price (context.wholesale_price
    is None) is NOT treated as a context-level validation error here. It
    is an evidentiary gap (Phase 6A's evaluate_group already ABSTAINs on
    it at the group-evaluation stage, Phase 5D Section 9), not a
    structural malformation of the request -- and Phase 5E's eligibility
    filter (Section 4) and this phase's own Step 5 "authoritative fields"
    list (q_i, L_i, H_i,c) do not name it as a vendor-eligibility
    criterion either. This is a deliberate scope boundary, not an
    oversight -- see reports/phase6b_validation_and_eligibility_report.md,
    Section 16.
    """
    reasons = []

    if not context.commodity_id or not context.commodity_id.strip():
        reasons.append(ContextValidationReason.MISSING_COMMODITY.value)

    if not context.date or not context.date.strip():
        reasons.append(ContextValidationReason.MALFORMED_CONTEXT_METADATA.value)

    if vendor_submissions is None or len(vendor_submissions) == 0:
        reasons.append(ContextValidationReason.EMPTY_VENDOR_COLLECTION.value)
    else:
        for v in vendor_submissions:
            if not isinstance(v, VendorSubmission) or not v.vendor_id or not v.vendor_id.strip():
                reasons.append(ContextValidationReason.MALFORMED_VENDOR_COLLECTION.value)
                break

    return ContextValidationResult(is_valid=(len(reasons) == 0), reasons=reasons)


def validate_vendor_structure(submission: VendorSubmission) -> Optional[str]:
    """Structural (VALIDATION_ERROR-tier) checks on ONE vendor submission.
    Returns a ValidationErrorReason value if malformed, else None.
    Does NOT check evidence sufficiency (e.g. an empty diary is not an
    error here -- see eligibility.py, which routes that to ABSTAIN)."""

    loc = submission.location
    if loc.status != VendorLocationStatus.MISSING:
        if loc.lat is None or loc.lon is None:
            return ValidationErrorReason.MALFORMED_LOCATION.value
        if not (-90.0 <= loc.lat <= 90.0) or not (-180.0 <= loc.lon <= 180.0):
            return ValidationErrorReason.MALFORMED_LOCATION.value

    if submission.individual_price_rs_per_kg is not None and submission.individual_price_rs_per_kg < 0:
        return ValidationErrorReason.NEGATIVE_QUANTITY.value

    if submission.user_provided_q_i is not None and submission.user_provided_q_i < 0:
        return ValidationErrorReason.NEGATIVE_QUANTITY.value

    if submission.practical_horizon_days is not None and submission.practical_horizon_days <= 0:
        return ValidationErrorReason.INVALID_NUMERIC_VALUE.value

    return None
