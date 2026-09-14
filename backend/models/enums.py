"""
Enumerations for the collaborative procurement decision system.

Authoritative sources (nothing here invents a new category):
  - DecisionState:            Phase 5D, Section 9 (the four decision states)
  - EstimationProvenance:     Phase 5C Sections 6-7 / Phase 5D Section 3
  - PriceGeographicLevel:     Phase 5A's Data Granularity Rule / Phase 5D Section 4a
  - VendorLocationStatus:     Phase 5G Section 5 (formalizing Phase 1C's Option A / Option B)

Two axes are kept explicitly separate, per Phase 5G Section 5:
  Axis 1 (PriceGeographicLevel) describes where a PRICE figure came from.
  Axis 2 (VendorLocationStatus) describes a VENDOR's own location precision.
These must never be confused or merged.
"""

from enum import Enum


class DecisionState(str, Enum):
    """The four, mutually-exclusive procurement decision states.
    Authoritative source: Phase 5D Section 9; evaluation order fixed there
    and restated in Phase 5E Section 16."""
    BUY_TOGETHER = "BUY_TOGETHER"
    WAIT_OR_EXPAND_GROUP = "WAIT_OR_EXPAND_GROUP"
    DO_NOT_BUY_TOGETHER = "DO_NOT_BUY_TOGETHER"
    ABSTAIN = "ABSTAIN"


class EstimationProvenance(str, Enum):
    """Where a vendor's demand estimate q_i came from.
    Authoritative source: Phase 5C Sections 6-7, Phase 5D Section 3.
    ESTIMATE_ML is a defined-but-currently-unused slot -- Phase 5C's Section 12
    verdict is that ML is not justified for this project's current data, so
    no code path in this project may ever produce this value.

    USER_PROVIDED added in Phase 6B: Phase 5D Section 2's own notation
    table already lists q_i's possible status as "Real (diary) /
    User-provided (survey) / Estimated (cold-start)" -- a direct,
    one-time survey-stated quantity is a distinct provenance from a
    diary-derived baseline estimate, and Phase 6A's enum had not yet
    needed to represent it (Phase 6A never received a raw, pre-estimation
    vendor submission). This is an additive closing of a demonstrable gap
    against the authoritative notation, not a new invented category --
    see reports/phase6b_validation_and_eligibility_report.md, Section 7."""
    USER_PROVIDED = "USER_PROVIDED"
    ESTIMATE_COLD_START = "ESTIMATE_COLD_START"
    ESTIMATE_BASELINE = "ESTIMATE_BASELINE"
    ESTIMATE_ML = "ESTIMATE_ML"  # defined, never produced (Phase 5C Section 12)


class PriceGeographicLevel(str, Enum):
    """Axis 1: geographic granularity of a PRICE/market-data figure.
    Authoritative source: Phase 5A's Data Granularity Rule; Phase 5D Section 4a.
    A DISTRICT_LEVEL_PROXY value must never be silently re-tagged MANDI_LEVEL."""
    MANDI_LEVEL = "MANDI_LEVEL"
    DISTRICT_LEVEL_PROXY = "DISTRICT_LEVEL_PROXY"
    UNKNOWN_GRANULARITY = "UNKNOWN_GRANULARITY"


class VendorLocationStatus(str, Enum):
    """Axis 2: precision status of a VENDOR's own location.
    Authoritative source: Phase 5G Section 5, formalizing Phase 1C Section 3 (C4):
      Option A -> VENDOR_SPECIFIC_APPROXIMATE (recommended, current V1 default)
      Option B -> LOCALITY_CENTROID_PROXY (fallback only, less accurate)
      no coordinate recorded -> MISSING
    No tier claims survey-grade/GPS-exact precision (Phase 5G Section 5)."""
    VENDOR_SPECIFIC_APPROXIMATE = "VENDOR_SPECIFIC_APPROXIMATE"
    LOCALITY_CENTROID_PROXY = "LOCALITY_CENTROID_PROXY"
    MISSING = "MISSING"


class OutcomeKind(str, Enum):
    """Distinguishes a legitimate ABSTAIN (insufficient evidence) from a
    VALIDATION_ERROR (malformed/out-of-range input). These must never be
    conflated -- Phase 5F Module Interfaces Section 4; Phase 5G Section 7."""
    OK = "OK"
    ABSTAIN = "ABSTAIN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
