"""
Batch-level data contracts for Phase 6B's validation and eligibility
pipeline.

These are NEW in Phase 6B -- they represent the stage BEFORE Phase 6A's
VendorInput (which already assumes q_i has been resolved). Phase 6B
consumes a VendorSubmission (raw, pre-estimation) and, for eligible
vendors, PRODUCES a Phase 6A VendorInput unchanged (reused, not
duplicated) -- see backend/services/eligibility.py.

Authoritative source: Phase 5F Module Interfaces Section 1 (input
contract shape); Phase 5E Section 2 (vendor universe fields).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from backend.models.contracts import ProcurementContext, TaggedLocation, VendorInput
from backend.models.enums import EstimationProvenance


@dataclass(frozen=True)
class VendorSubmission:
    """One vendor's RAW input, as submitted, before demand estimation or
    eligibility determination runs. Distinct from Phase 6A's VendorInput,
    which represents the resolved, post-estimation state.

    Exactly one of user_provided_q_i / diary_records / peer_q_values is
    expected to carry data in the typical case, per the demand hierarchy
    (Phase 5C Sections 6-7) -- but this contract does not enforce that;
    validation.py and eligibility.py decide precedence and handle absence.
    """
    vendor_id: str
    location: TaggedLocation
    individual_price_rs_per_kg: Optional[float]
    practical_horizon_days: Optional[int]
    user_provided_q_i: Optional[float] = None
    diary_records: Optional[Sequence[float]] = None
    peer_q_values: Optional[Sequence[float]] = None


@dataclass
class VendorEligibilityResult:
    """The single structured outcome for one vendor (Phase 6B's
    'IMPORTANT RESULT RULE' -- one outcome per vendor)."""
    vendor_id: str
    status: str  # OutcomeKind value: OK (eligible) / ABSTAIN / VALIDATION_ERROR
    eligible: bool
    vendor_input: Optional[VendorInput]  # populated only when eligible=True
    demand_provenance: Optional[EstimationProvenance]
    reason_code: Optional[str]  # AbstentionReason / ValidationErrorReason value, or None if eligible
    reason_detail: str


@dataclass
class ContextValidationResult:
    """Structural validity of a procurement context and its vendor
    collection, checked BEFORE any per-vendor processing (Phase 6B Step 2)."""
    is_valid: bool
    reasons: List[str] = field(default_factory=list)  # ContextValidationReason values


@dataclass
class BatchEligibilityResult:
    """The full batch outcome for one procurement context.
    Authoritative source: Phase 6B Step 7 -- eligible / abstained /
    validation-error vendors are kept in separate collections; a
    structurally invalid context stops processing before any vendor list
    is populated."""
    context: ProcurementContext
    context_validation: ContextValidationResult
    eligible_vendors: List[VendorEligibilityResult] = field(default_factory=list)
    abstained_vendors: List[VendorEligibilityResult] = field(default_factory=list)
    validation_error_vendors: List[VendorEligibilityResult] = field(default_factory=list)
