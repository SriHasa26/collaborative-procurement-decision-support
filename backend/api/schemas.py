"""
Phase 6F -- API request schema and its converter into the existing domain
contracts.

These Pydantic models exist ONLY as the HTTP/JSON validation boundary
(Layer 1: malformed JSON, wrong type, missing required field) -- they
carry exactly the fields Phase 6B/6C/6D's existing contracts already
require, reusing the project's own Enums (VendorLocationStatus,
PriceGeographicLevel) directly rather than redefining them. No field is
invented, and no vendor personal information (name, phone, address,
payment detail) is accepted, since none of that exists anywhere in the
underlying VendorSubmission contract either.

CRITICAL BOUNDARY: none of these models perform DOMAIN validation.
Negative quantities, out-of-range coordinates, and missing evidence are
NOT rejected here -- validate_vendor_structure/evaluate_vendor
(Phase 6B, unmodified) already handle exactly that, routing each affected
vendor to a VALIDATION_ERROR or ABSTAIN outcome without blocking the rest
of the batch. Adding numeric-range constraints here would silently move a
domain rule into the API layer and turn a legitimate per-vendor outcome
into an HTTP 422 for the whole request -- Phase 6F Section 10 explicitly
forbids this.
"""

from typing import List, Optional, Tuple

from pydantic import BaseModel

from backend.models.batch_contracts import VendorSubmission
from backend.models.contracts import (
    CommodityParams,
    ConfigParams,
    ProcurementContext,
    TaggedLocation,
    TaggedPrice,
    TransportTier,
)
from backend.models.enums import PriceGeographicLevel, VendorLocationStatus
from backend.models.run_contracts import ProcurementRunInput


class TaggedLocationRequest(BaseModel):
    status: VendorLocationStatus
    lat: Optional[float] = None
    lon: Optional[float] = None


class VendorSubmissionRequest(BaseModel):
    vendor_id: str
    location: TaggedLocationRequest
    individual_price_rs_per_kg: Optional[float] = None
    practical_horizon_days: Optional[int] = None
    user_provided_q_i: Optional[float] = None
    diary_records: Optional[List[float]] = None
    peer_q_values: Optional[List[float]] = None


class TaggedPriceRequest(BaseModel):
    value_rs_per_kg: float
    geographic_level: PriceGeographicLevel


class ProcurementContextRequest(BaseModel):
    commodity_id: str
    date: str
    wholesale_price: Optional[TaggedPriceRequest] = None


class CommodityParamsRequest(BaseModel):
    commodity_id: str
    freshness_window_days: Optional[int] = None
    moq_kg: Optional[float] = None


class TransportTierRequest(BaseModel):
    capacity_kg: float
    cost_rs: float


class ConfigParamsRequest(BaseModel):
    d_max_km: float
    trader_margin: float
    transport_tiers: List[TransportTierRequest]


class ProcurementAnalysisRequest(BaseModel):
    """One request represents exactly one (commodity, procurement context,
    vendor universe) run, per Phase 5E's own definition -- commodity
    isolation is structural here: a request has exactly one `commodity`
    and one `context`, and `vendor_submissions` carries no separate
    commodity tag that could be used to smuggle a second commodity in."""
    commodity: CommodityParamsRequest
    context: ProcurementContextRequest
    vendor_submissions: List[VendorSubmissionRequest]
    config: ConfigParamsRequest


def build_run_input(payload: ProcurementAnalysisRequest) -> ProcurementRunInput:
    """Pure conversion from the validated API request into the existing
    ProcurementRunInput domain contract. No business rule is evaluated
    here -- every field is copied through as-is."""
    commodity = CommodityParams(
        commodity_id=payload.commodity.commodity_id,
        freshness_window_days=payload.commodity.freshness_window_days,
        moq_kg=payload.commodity.moq_kg,
    )

    wholesale_price: Optional[TaggedPrice] = None
    if payload.context.wholesale_price is not None:
        wholesale_price = TaggedPrice(
            value_rs_per_kg=payload.context.wholesale_price.value_rs_per_kg,
            geographic_level=payload.context.wholesale_price.geographic_level,
        )
    context = ProcurementContext(
        commodity_id=payload.context.commodity_id,
        date=payload.context.date,
        wholesale_price=wholesale_price,
    )

    vendor_submissions: Tuple[VendorSubmission, ...] = tuple(
        VendorSubmission(
            vendor_id=v.vendor_id,
            location=TaggedLocation(status=v.location.status, lat=v.location.lat, lon=v.location.lon),
            individual_price_rs_per_kg=v.individual_price_rs_per_kg,
            practical_horizon_days=v.practical_horizon_days,
            user_provided_q_i=v.user_provided_q_i,
            diary_records=tuple(v.diary_records) if v.diary_records is not None else None,
            peer_q_values=tuple(v.peer_q_values) if v.peer_q_values is not None else None,
        )
        for v in payload.vendor_submissions
    )

    config = ConfigParams(
        d_max_km=payload.config.d_max_km,
        trader_margin=payload.config.trader_margin,
        transport_tiers=tuple(
            TransportTier(capacity_kg=t.capacity_kg, cost_rs=t.cost_rs) for t in payload.config.transport_tiers
        ),
    )

    return ProcurementRunInput(commodity=commodity, context=context, vendor_submissions=vendor_submissions, config=config)
