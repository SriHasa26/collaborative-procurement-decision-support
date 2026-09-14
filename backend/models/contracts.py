"""
Core data contracts for the collaborative procurement decision system.

Authoritative source: Phase 5F Module Interfaces, Section 1 (Input Data
Contract) and Section 2 (Output Contract). These are interface/data
contracts, not a database schema -- no storage engine, indexing, or
persistence decision is made here (Phase 5F Module Interfaces, Section 1).

Only fields actually required for Phase 6A's scope (demand estimation and
single-group decision-engine math) are included. No personal information
is stored -- location is an anonymous, vendor_id-scoped coordinate only
(Phase 5E Section 2; Phase 1C's privacy design).
"""

from dataclasses import dataclass, field
from typing import Optional

from backend.models.enums import (
    EstimationProvenance,
    PriceGeographicLevel,
    VendorLocationStatus,
)


@dataclass(frozen=True)
class TaggedLocation:
    """A vendor's location, always carrying its precision status.
    Coordinates are (lat, lon) in decimal degrees, or None if status is MISSING.
    The status must never be silently upgraded (Phase 5G Section 5/7)."""
    status: VendorLocationStatus
    lat: Optional[float] = None
    lon: Optional[float] = None

    def is_usable(self) -> bool:
        """Usable for geographic compatibility math means a coordinate
        exists -- both VENDOR_SPECIFIC_APPROXIMATE and LOCALITY_CENTROID_PROXY
        are usable; MISSING is not (Phase 5E Section 4)."""
        return self.status != VendorLocationStatus.MISSING and self.lat is not None and self.lon is not None


@dataclass(frozen=True)
class TaggedPrice:
    """A price figure, always carrying its geographic-granularity tag.
    Authoritative source: Phase 5D Section 4a -- a DISTRICT_LEVEL_PROXY value
    must never be presented or treated as MANDI_LEVEL."""
    value_rs_per_kg: float
    geographic_level: PriceGeographicLevel


@dataclass(frozen=True)
class VendorInput:
    """One vendor's data as required for a single procurement-context
    evaluation. Authoritative source: Phase 5F Module Interfaces Section 1A;
    Phase 5E Section 2 (vendor universe)."""
    vendor_id: str
    location: TaggedLocation
    q_i: Optional[float]  # demand estimate, kg/day; None if not yet estimated
    estimation_provenance: Optional[EstimationProvenance]
    individual_price_rs_per_kg: Optional[float]  # p_ind_i,c
    practical_horizon_days: Optional[int]  # H_i,c (direct or proxy-derived)


@dataclass(frozen=True)
class CommodityParams:
    """Commodity-level parameters for one (commodity, date) context.
    Authoritative source: Phase 5F Module Interfaces Section 1B; Phase 5D Section 2.
    moq_kg is intentionally Optional -- absence means the MOQ constraint is
    simply not applied (Phase 2A Part 18; Phase 5D Section 5), never defaulted."""
    commodity_id: str
    freshness_window_days: Optional[int]  # F_c; None means "does not bind" (e.g. long shelf life)
    moq_kg: Optional[float] = None  # MOQ_c -- present only if trader-confirmed


@dataclass(frozen=True)
class TransportTier:
    """One vehicle-capacity tier. Authoritative source: Phase 2A Part 13 /
    Phase 5D Section 7. capacity_kg is the tier's upper bound; cost_rs is the
    flat per-trip charge for that tier."""
    capacity_kg: float
    cost_rs: float


@dataclass(frozen=True)
class ConfigParams:
    """Configurable prototype parameters (Phase 5F Module Interfaces Section 1E).
    None of these is an unsupported hardcoded real-world constant -- each is
    explicitly labeled configurable, per Phase 5D Section 11 / Phase 5F Section 10."""
    d_max_km: float
    trader_margin: float  # m, one of {0, 0.10, 0.15} per Phase 2A Part 7
    transport_tiers: tuple  # tuple[TransportTier, ...], ordered by capacity_kg ascending


@dataclass(frozen=True)
class ProcurementContext:
    """One (commodity, date) evaluation context.
    Authoritative source: Phase 5D Section 3; Phase 5E Section 3."""
    commodity_id: str
    date: str  # ISO date string, e.g. "2026-09-14"
    wholesale_price: Optional[TaggedPrice]  # p_wh_c,t -- None if unavailable for this date


@dataclass(frozen=True)
class CandidateGroup:
    """An already-formed candidate group of vendors for one procurement
    context. Group FORMATION (how this list was produced) is explicitly out
    of Phase 6A's scope (Phase 2B; Phase 5E Sections 5-6) -- this contract
    only represents a group as GIVEN input to the single-group Decision
    Engine (Phase 5F Module Interfaces Section 3, "Procurement Decision
    Engine")."""
    group_id: str
    members: tuple  # tuple[VendorInput, ...]


@dataclass
class PerVendorAllocation:
    """One vendor's cost share and savings within a BUY_TOGETHER group.
    Authoritative source: Phase 5D Section 4 (quantity-proportional allocation)."""
    vendor_id: str
    share_rs: float
    individual_savings_rs: float
    consumption_time_days: float  # Phase 5D Section 6: equals k exactly


@dataclass
class GroupDecisionResult:
    """The full output of evaluating one candidate group.
    Authoritative source: Phase 5F Module Interfaces Section 2 (per_group_result).
    Populated fields depend on decision_state -- see Phase 5D Section 9."""
    group_id: str
    decision_state: str  # DecisionState value
    reason: str
    k_star: Optional[int] = None
    aggregate_quantity_kg: Optional[float] = None  # Q_G(k*)
    moq_applicable: Optional[bool] = None
    moq_met: Optional[bool] = None
    moq_shortfall_kg: Optional[float] = None  # only for WAIT_OR_EXPAND_GROUP
    centroid_distance_km: Optional[float] = None
    within_d_max: Optional[bool] = None
    individual_cost_total_rs: Optional[float] = None
    collaborative_cost_rs: Optional[float] = None
    savings_rs: Optional[float] = None
    per_vendor_allocation: Optional[list] = field(default=None)  # list[PerVendorAllocation]
