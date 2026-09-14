"""
Phase 6E fixtures: application-level orchestration
(ProcurementRunService.run).

SIMULATED ILLUSTRATIVE FIXTURE DATA -- every value below is invented for
testing only and does not represent a real vendor.

These are VendorSubmission (Phase 6B, raw/pre-estimation) instances, since
Phase 6E's public input contract (ProcurementRunInput) carries submissions,
not already-resolved Phase 6A VendorInput -- the whole point of Phase 6E is
to run the REAL Phase 6B validation/estimation/eligibility step, not to
bypass it. Reuses Phase 6A/6B's existing contracts (TaggedLocation,
TaggedPrice, CommodityParams, ProcurementContext, ConfigParams,
VendorSubmission) directly -- no second vendor or context schema.
"""

from backend.models.contracts import (
    CommodityParams,
    ConfigParams,
    ProcurementContext,
    TaggedLocation,
    TaggedPrice,
    TransportTier,
)
from backend.models.batch_contracts import VendorSubmission
from backend.models.enums import PriceGeographicLevel, VendorLocationStatus

COMMODITY_ID = "tomato"
CONTEXT_DATE = "2026-orchestration-test"

COMMODITY = CommodityParams(commodity_id=COMMODITY_ID, freshness_window_days=None, moq_kg=None)
CONTEXT = ProcurementContext(
    commodity_id=COMMODITY_ID,
    date=CONTEXT_DATE,
    wholesale_price=TaggedPrice(value_rs_per_kg=15.0, geographic_level=PriceGeographicLevel.MANDI_LEVEL),
)
CONFIG = ConfigParams(
    d_max_km=2.0,
    trader_margin=0.10,
    transport_tiers=(TransportTier(capacity_kg=100_000, cost_rs=800.0),),
)

# A different commodity/context/config, for T7 commodity-isolation testing.
OTHER_COMMODITY_ID = "onion"
OTHER_COMMODITY = CommodityParams(commodity_id=OTHER_COMMODITY_ID, freshness_window_days=None, moq_kg=None)
OTHER_CONTEXT = ProcurementContext(
    commodity_id=OTHER_COMMODITY_ID,
    date=CONTEXT_DATE,
    wholesale_price=TaggedPrice(value_rs_per_kg=12.0, geographic_level=PriceGeographicLevel.MANDI_LEVEL),
)

LOCATION_CLUSTER = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.45, lon=78.47)
# Two mutually-incompatible locations, each far from the cluster AND far
# from each other -- used for the "no geographic compatibility" scenario.
LOCATION_FAR_A = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=20.0, lon=80.0)
LOCATION_FAR_B = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=25.0, lon=85.0)


# --- Eligible, mutually compatible, individual price well above the
# effective wholesale price (15.0 * 1.10 = 16.5 Rs/kg) -- collaboration is
# genuinely economically favorable, no MOQ configured. ---
ELIGIBLE_1 = VendorSubmission(
    vendor_id="ELIGIBLE_1", location=LOCATION_CLUSTER,
    individual_price_rs_per_kg=25.0, practical_horizon_days=5, user_provided_q_i=10.0,
)
ELIGIBLE_2 = VendorSubmission(
    vendor_id="ELIGIBLE_2", location=LOCATION_CLUSTER,
    individual_price_rs_per_kg=26.0, practical_horizon_days=5, user_provided_q_i=8.0,
)
ELIGIBLE_3 = VendorSubmission(
    vendor_id="ELIGIBLE_3", location=LOCATION_CLUSTER,
    individual_price_rs_per_kg=24.0, practical_horizon_days=5, user_provided_q_i=12.0,
)

# --- ABSTAIN: structurally valid, but no demand evidence at all. ---
ABSTAIN_NO_EVIDENCE = VendorSubmission(
    vendor_id="ABSTAIN_NO_EVIDENCE", location=LOCATION_CLUSTER,
    individual_price_rs_per_kg=20.0, practical_horizon_days=5,
)

# --- VALIDATION_ERROR: a negative diary quantity -- malformed input. ---
VALIDATION_ERROR_NEGATIVE_QTY = VendorSubmission(
    vendor_id="VALIDATION_ERROR_NEGATIVE_QTY", location=LOCATION_CLUSTER,
    individual_price_rs_per_kg=20.0, practical_horizon_days=5, diary_records=(-5.0,),
)

# --- Eligible but geographically isolated from each other (for the
# "no compatible vendors" scenario -- both individually valid, zero shared
# compatibility edges). ---
FAR_A = VendorSubmission(
    vendor_id="FAR_A", location=LOCATION_FAR_A,
    individual_price_rs_per_kg=25.0, practical_horizon_days=5, user_provided_q_i=10.0,
)
FAR_B = VendorSubmission(
    vendor_id="FAR_B", location=LOCATION_FAR_B,
    individual_price_rs_per_kg=25.0, practical_horizon_days=5, user_provided_q_i=10.0,
)

# --- Eligible, mutually compatible, but individual price BELOW the
# effective wholesale price -- collaboration is never economically
# favorable, so candidate groups form but none reach BUY_TOGETHER. ---
LOW_PRICE_1 = VendorSubmission(
    vendor_id="LOW_PRICE_1", location=LOCATION_CLUSTER,
    individual_price_rs_per_kg=10.0, practical_horizon_days=5, user_provided_q_i=10.0,
)
LOW_PRICE_2 = VendorSubmission(
    vendor_id="LOW_PRICE_2", location=LOCATION_CLUSTER,
    individual_price_rs_per_kg=11.0, practical_horizon_days=5, user_provided_q_i=8.0,
)
