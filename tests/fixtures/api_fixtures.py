"""
Phase 6F fixtures: JSON request payloads for the /procurement/analyze
endpoint.

SIMULATED ILLUSTRATIVE FIXTURE DATA -- every value below is invented for
testing only and does not represent a real vendor.

These are plain dicts (the exact JSON shape a real HTTP client would send)
carrying the SAME underlying vendor economics already used and verified in
tests/fixtures/orchestration_fixtures.py (Phase 6E) -- same coordinates,
same prices, same demand quantities -- so the already-known pipeline
outcomes (which vendors are eligible/abstain/error, which groups reach
BUY_TOGETHER) carry over directly; nothing new is being asserted about the
math here, only that the API layer transports it faithfully.
"""

COMMODITY_ID = "tomato"
CONTEXT_DATE = "2026-orchestration-test"

_CLUSTER_LAT, _CLUSTER_LON = 17.45, 78.47
_FAR_A_LAT, _FAR_A_LON = 20.0, 80.0
_FAR_B_LAT, _FAR_B_LON = 25.0, 85.0


def _vendor_payload(vendor_id, lat, lon, price, horizon=5, q=None, diary=None, peers=None):
    return {
        "vendor_id": vendor_id,
        "location": {"status": "VENDOR_SPECIFIC_APPROXIMATE", "lat": lat, "lon": lon},
        "individual_price_rs_per_kg": price,
        "practical_horizon_days": horizon,
        "user_provided_q_i": q,
        "diary_records": diary,
        "peer_q_values": peers,
    }


def build_request_payload(vendor_payloads, commodity_id=COMMODITY_ID, moq_kg=None, wholesale_price=15.0):
    return {
        "commodity": {"commodity_id": commodity_id, "freshness_window_days": None, "moq_kg": moq_kg},
        "context": {
            "commodity_id": commodity_id,
            "date": CONTEXT_DATE,
            "wholesale_price": {"value_rs_per_kg": wholesale_price, "geographic_level": "MANDI_LEVEL"},
        },
        "vendor_submissions": vendor_payloads,
        "config": {
            "d_max_km": 2.0,
            "trader_margin": 0.10,
            "transport_tiers": [{"capacity_kg": 100000, "cost_rs": 800.0}],
        },
    }


# --- Eligible, mutually compatible, individual price well above the
# effective wholesale price (15.0 * 1.10 = 16.5 Rs/kg). ---
ELIGIBLE_1 = _vendor_payload("ELIGIBLE_1", _CLUSTER_LAT, _CLUSTER_LON, 25.0, q=10.0)
ELIGIBLE_2 = _vendor_payload("ELIGIBLE_2", _CLUSTER_LAT, _CLUSTER_LON, 26.0, q=8.0)
ELIGIBLE_3 = _vendor_payload("ELIGIBLE_3", _CLUSTER_LAT, _CLUSTER_LON, 24.0, q=12.0)

# --- ABSTAIN: no demand evidence at all. ---
ABSTAIN_NO_EVIDENCE = _vendor_payload("ABSTAIN_NO_EVIDENCE", _CLUSTER_LAT, _CLUSTER_LON, 20.0)

# --- VALIDATION_ERROR: a negative diary quantity (domain-level, not
# API-level, malformed data). ---
VALIDATION_ERROR_NEGATIVE_QTY = _vendor_payload(
    "VALIDATION_ERROR_NEGATIVE_QTY", _CLUSTER_LAT, _CLUSTER_LON, 20.0, diary=[-5.0]
)

# --- Eligible but geographically mutually incompatible. ---
FAR_A = _vendor_payload("FAR_A", _FAR_A_LAT, _FAR_A_LON, 25.0, q=10.0)
FAR_B = _vendor_payload("FAR_B", _FAR_B_LAT, _FAR_B_LON, 25.0, q=10.0)

# --- Eligible, compatible, but individual price BELOW the effective
# wholesale price -- collaboration is never economically favorable. ---
LOW_PRICE_1 = _vendor_payload("LOW_PRICE_1", _CLUSTER_LAT, _CLUSTER_LON, 10.0, q=10.0)
LOW_PRICE_2 = _vendor_payload("LOW_PRICE_2", _CLUSTER_LAT, _CLUSTER_LON, 11.0, q=8.0)
