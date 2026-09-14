"""
Batch-level orchestration -- takes a procurement context plus a collection
of raw vendor submissions and produces one structured batch result.

Scope discipline (Phase 6B Step 15): this module orchestrates only. It
calls validation.py and eligibility.py; it contains no cost/savings math,
no demand-estimation math, no geographic math, and no group-formation
logic of its own.

CORE DESIGN PRINCIPLE (Phase 6B): each vendor is evaluated independently.
One vendor's structural error or evidentiary gap must never prevent
unrelated valid vendors from being processed and returned as eligible.
This is enforced here by wrapping each vendor's evaluation in its own
try/except, in addition to eligibility.evaluate_vendor's own internal
exception handling -- defense in depth, not duplicated logic (the outer
except here only catches a truly unexpected error eligibility.py itself
did not anticipate; it is not expected to ever trigger in normal use).
"""

from typing import List

from backend.models.batch_contracts import BatchEligibilityResult, VendorEligibilityResult, VendorSubmission
from backend.models.contracts import ProcurementContext
from backend.models.enums import OutcomeKind
from backend.services import validation
from backend.services.eligibility import evaluate_vendor


def evaluate_procurement_context(
    context: ProcurementContext,
    vendor_submissions: List[VendorSubmission],
) -> BatchEligibilityResult:
    """Full Phase 6B pipeline for one procurement context.

    If the context itself is structurally invalid (Phase 6B Step 2), no
    per-vendor processing is attempted at all -- the batch result carries
    only the context-validation failure, with empty vendor collections,
    per this phase's explicit "do not silently continue with meaningless
    input" instruction."""

    context_validation = validation.validate_context(context, vendor_submissions)
    if not context_validation.is_valid:
        return BatchEligibilityResult(
            context=context,
            context_validation=context_validation,
            eligible_vendors=[],
            abstained_vendors=[],
            validation_error_vendors=[],
        )

    eligible: List[VendorEligibilityResult] = []
    abstained: List[VendorEligibilityResult] = []
    validation_errors: List[VendorEligibilityResult] = []

    for submission in vendor_submissions:
        try:
            result = evaluate_vendor(submission, context)
        except Exception as exc:  # defense in depth -- see module docstring
            result = VendorEligibilityResult(
                vendor_id=getattr(submission, "vendor_id", "<unknown>"),
                status=OutcomeKind.VALIDATION_ERROR.value,
                eligible=False,
                vendor_input=None,
                demand_provenance=None,
                reason_code="UNEXPECTED_ERROR",
                reason_detail=f"unexpected error during evaluation: {exc}",
            )

        if result.status == OutcomeKind.OK.value:
            eligible.append(result)
        elif result.status == OutcomeKind.ABSTAIN.value:
            abstained.append(result)
        else:
            validation_errors.append(result)

    return BatchEligibilityResult(
        context=context,
        context_validation=context_validation,
        eligible_vendors=eligible,
        abstained_vendors=abstained,
        validation_error_vendors=validation_errors,
    )
