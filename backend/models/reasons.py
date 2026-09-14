"""
Named, machine-readable reason codes for non-eligible outcomes.

New in Phase 6B -- these do not exist in Phase 6A and do not duplicate
anything there. Phase 6A's own outcome types (OutcomeKind: OK/ABSTAIN/
VALIDATION_ERROR) are reused unchanged; these enums only name *which*
specific reason applies within those outcome kinds (Phase 6B Step 8).
"""

from enum import Enum


class ValidationErrorReason(str, Enum):
    """Reasons for a vendor-level VALIDATION_ERROR -- malformed or
    logically invalid input (Phase 6B Step 3A)."""
    NEGATIVE_QUANTITY = "NEGATIVE_QUANTITY"
    INVALID_NUMERIC_VALUE = "INVALID_NUMERIC_VALUE"
    MALFORMED_LOCATION = "MALFORMED_LOCATION"


class AbstentionReason(str, Enum):
    """Reasons for a vendor-level ABSTAIN -- structurally valid input,
    insufficient critical evidence (Phase 6B Step 3B; Phase 5E Section 4)."""
    INSUFFICIENT_DEMAND_EVIDENCE = "INSUFFICIENT_DEMAND_EVIDENCE"
    MISSING_LOCATION = "MISSING_LOCATION"
    MISSING_HORIZON = "MISSING_HORIZON"


class ContextValidationReason(str, Enum):
    """Reasons a procurement context itself is structurally invalid
    (Phase 6B Step 2) -- these stop the entire batch before any per-vendor
    processing is attempted."""
    MISSING_COMMODITY = "MISSING_COMMODITY"
    EMPTY_VENDOR_COLLECTION = "EMPTY_VENDOR_COLLECTION"
    MALFORMED_VENDOR_COLLECTION = "MALFORMED_VENDOR_COLLECTION"
    MALFORMED_CONTEXT_METADATA = "MALFORMED_CONTEXT_METADATA"
