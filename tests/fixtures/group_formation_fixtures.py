"""
Phase 6C group-formation fixtures.

SIMULATED ILLUSTRATIVE FIXTURE DATA -- every coordinate below is invented
for testing only and does not represent a real vendor's location.

COORDINATE METHOD (learned from Phase 6A -- see
tests/unit/test_decision_engine_regression.py's header comment): every
coordinate here is a REAL (lat, lon) pair in decimal degrees, converted
from an intended straight-line kilometer offset around an illustrative
Hyderabad-area base point (17.45N, 78.47E) using the same flat-plane
approximation Phase 6A verified is accurate at sub-10km scale. Every
resulting Haversine distance was independently computed and confirmed
BEFORE being written into this file (not estimated afterward) -- see the
distance comment on each fixture below.

D_MAX_KM = 2.0 throughout (consistent with prior phases), so the pairwise
compatibility threshold (2 * D_max) is 4.0 km.
"""

from backend.models.contracts import ConfigParams, TransportTier, VendorInput
from backend.models.enums import VendorLocationStatus
from backend.models.contracts import TaggedLocation

D_MAX_KM = 2.0
CONFIG = ConfigParams(d_max_km=D_MAX_KM, trader_margin=0.10, transport_tiers=(TransportTier(100000, 800.0),))


def _vendor(vendor_id, lat, lon, q=10.0, p_ind=25.0, h=5):
    return VendorInput(
        vendor_id=vendor_id,
        location=TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=lat, lon=lon),
        q_i=q,
        estimation_provenance=None,
        individual_price_rs_per_kg=p_ind,
        practical_horizon_days=h,
    )


# --- TEST 1: exact compatible pair (distance ~0.99 km <= 4.0 km) ---
T1_A = _vendor("T1_A", 17.45, 78.47)
T1_B = _vendor("T1_B", 17.45630631, 78.47661053)

# --- TEST 2: exact incompatible pair (distance ~10.02 km > 4.0 km) ---
T2_A = _vendor("T2_A", 17.45, 78.47)
T2_B = _vendor("T2_B", 17.45, 78.56443614)

# --- TEST 4 / TEST 8: three-vendor chain ---
# CHAIN_A-CHAIN_B ~3.01 km (compatible); CHAIN_B-CHAIN_C ~3.01 km (compatible);
# CHAIN_A-CHAIN_C ~6.01 km (NOT compatible, > 4.0 km).
# One connected component via the CHAIN_B bridge; A and C are NOT a direct edge.
CHAIN_A = _vendor("CHAIN_A", 17.45, 78.47)
CHAIN_B = _vendor("CHAIN_B", 17.45, 78.49833084)
CHAIN_C = _vendor("CHAIN_C", 17.45, 78.52666168)

# --- TEST 5: two disconnected pools ---
# Pool 1 internal distance ~1.00 km (compatible); Pool 2 internal distance
# ~1.00 km (compatible); the two pools are ~70.8 km apart (NOT compatible).
POOL1_A = _vendor("POOL1_A", 17.45, 78.47)
POOL1_B = _vendor("POOL1_B", 17.45, 78.47944361)
POOL2_A = _vendor("POOL2_A", 17.90045045, 78.94218068)
POOL2_B = _vendor("POOL2_B", 17.90045045, 78.95162429)

# --- TEST 7: singleton -- isolated vendor, ~141.5 km from the chain cluster ---
SINGLETON = _vendor("SINGLETON", 18.3509009, 79.41436135)

# --- TEST 11: Phase 5E Section 15 worked example, reproduced exactly ---
# Coordinates identical to tests/unit/test_decision_engine_regression.py --
# NOT re-derived here, reused verbatim so both test files describe the
# same structural scenario consistently.
V1 = _vendor("V1", 17.45, 78.47, q=10.0, p_ind=30.0)
V2 = _vendor("V2", 17.4527027027027, 78.47472180675979, q=8.0, p_ind=28.0)
V3 = _vendor("V3", 17.454504504504502, 78.47944361351959, q=6.0, p_ind=32.0)
V4 = _vendor("V4", 17.45900900900901, 78.48416542027938, q=12.0, p_ind=29.0)
V7 = _vendor("V7", 17.445495495495496, 78.47755489081567, q=4.0, p_ind=31.0)
# V5 was isolated in Phase 5E's example (~13+ km from the others there);
# reusing that same designation here with a coordinate far from V1-V4/V7.
V5 = _vendor("V5", 18.3509009, 79.41436135, q=9.0, p_ind=31.0)
