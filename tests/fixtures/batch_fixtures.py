"""
Phase 6B batch-level fixtures.

SIMULATED ILLUSTRATIVE FIXTURE DATA -- every value below is invented for
testing only and does not represent a real vendor.

These build on, rather than duplicate, Phase 5G's D1-D4/G1-G4 fixture
DATA (tests/fixtures/demand_fixtures.py, tests/fixtures/geo_fixtures.py):
where the same underlying numbers apply, they are reused; new fixtures
here exist only to exercise the batch-level VendorSubmission shape and
the mixed-batch/context-validation behavior Phase 5G's fixtures did not
need to cover.
"""

from backend.models.batch_contracts import VendorSubmission
from backend.models.contracts import ProcurementContext, TaggedLocation, TaggedPrice
from backend.models.enums import PriceGeographicLevel, VendorLocationStatus

DEFAULT_LOCATION = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.4520, lon=78.4867)
DEFAULT_CONTEXT = ProcurementContext(
    commodity_id="potato",
    date="2026-09-14",
    wholesale_price=TaggedPrice(value_rs_per_kg=15.0, geographic_level=PriceGeographicLevel.MANDI_LEVEL),
)

# --- TEST 1: valid vendor, user-provided demand ---
VENDOR_USER_PROVIDED = VendorSubmission(
    vendor_id="T1_user_provided",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    user_provided_q_i=12.0,
)

# --- TEST 2: cold-start vendor with valid peers (reuses Phase 5G D1 numbers) ---
VENDOR_COLD_START = VendorSubmission(
    vendor_id="T2_cold_start",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=22.0,
    practical_horizon_days=5,
    peer_q_values=(8.0, 10.0, 9.0),  # Phase 5G D1 -- expected average 9.0
)

# --- TEST 3: >=3 diary records -> moving-average-3 (reuses Phase 5G D2 numbers) ---
VENDOR_MOVING_AVERAGE = VendorSubmission(
    vendor_id="T3_moving_average",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=21.0,
    practical_horizon_days=5,
    diary_records=(6.0, 9.0, 8.0),  # Phase 5G D2 -- expected 7.666...
)

# --- TEST 4: 1-2 diary records -> last-observed-value ---
VENDOR_LAST_OBSERVED = VendorSubmission(
    vendor_id="T4_last_observed",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=19.0,
    practical_horizon_days=5,
    diary_records=(11.0, 13.0),  # only 2 records -> last-observed-value = 13.0
)

# --- TEST 5: no history, no peers -> ABSTAIN / INSUFFICIENT_DEMAND_EVIDENCE ---
VENDOR_NO_EVIDENCE = VendorSubmission(
    vendor_id="T5_no_evidence",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
)

# --- TEST 6: negative quantity -> VALIDATION_ERROR ---
VENDOR_NEGATIVE_QUANTITY = VendorSubmission(
    vendor_id="T6_negative_quantity",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    diary_records=(-5.0,),
)

# --- TEST 7: missing critical location -> ABSTAIN / MISSING_LOCATION ---
VENDOR_MISSING_LOCATION = VendorSubmission(
    vendor_id="T7_missing_location",
    location=TaggedLocation(status=VendorLocationStatus.MISSING),
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    user_provided_q_i=10.0,
)

# --- TEST 8: missing critical horizon -> ABSTAIN / MISSING_HORIZON ---
VENDOR_MISSING_HORIZON = VendorSubmission(
    vendor_id="T8_missing_horizon",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=None,
    user_provided_q_i=10.0,
)

# --- Additional: locality-centroid proxy location (Phase 5G G3-adjacent, Axis 2) ---
VENDOR_LOCALITY_PROXY_LOCATION = VendorSubmission(
    vendor_id="T12_locality_proxy",
    location=TaggedLocation(status=VendorLocationStatus.LOCALITY_CENTROID_PROXY, lat=17.4600, lon=78.4900),
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    user_provided_q_i=10.0,
)

# --- Edge case: malformed location (out-of-range coordinate) -> VALIDATION_ERROR ---
VENDOR_MALFORMED_LOCATION = VendorSubmission(
    vendor_id="EDGE_malformed_location",
    location=TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=999.0, lon=78.4867),
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    user_provided_q_i=10.0,
)

# --- Edge case: diary contains an invalid (negative) value mixed with valid ones ---
VENDOR_DIARY_WITH_INVALID_VALUE = VendorSubmission(
    vendor_id="EDGE_diary_invalid_value",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    diary_records=(8.0, -2.0, 9.0),
)

# --- Edge case: peers containing an invalid (negative) value ---
VENDOR_PEERS_WITH_INVALID_VALUE = VendorSubmission(
    vendor_id="EDGE_peers_invalid_value",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    peer_q_values=(8.0, -3.0),
)

# --- Edge case: empty diary tuple explicitly given (vs None) -- must behave like no history ---
VENDOR_EMPTY_DIARY_TUPLE = VendorSubmission(
    vendor_id="EDGE_empty_diary_tuple",
    location=DEFAULT_LOCATION,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
    diary_records=(),
    peer_q_values=(),
)
