"""
Mathematical regression tests -- Phase 5E Section 15 worked example
(7-vendor potato scenario). This example supplies real illustrative
coordinates, so it is used to regression-test the FULL single-group
Decision Engine (geography + freshness/horizon + MOQ + economics + the
four decision states), unlike test_decision_math.py which uses Phase 5D's
Scenario 1 (no coordinates supplied there) for cost/savings math only.

SIMULATED ILLUSTRATIVE FIXTURE DATA -- reproduced from
reports/phase5e_group_formation_design.md, Section 15.

COORDINATE NOTE (a correction found during Phase 6A verification, not a
change to Phase 5E's math): Phase 5E's Section 15 described vendor
positions as small (x, y) KILOMETER-OFFSETS on an informal flat plane
("illustrative km-offset") and computed centroid distances with plain
Euclidean geometry on those offsets -- a valid approximation at sub-2km
scale. This test suite's Decision Engine calls the REAL Haversine formula
on (lat, lon) DEGREES, where 1 degree is ~111 km. Feeding the original
(0, 0), (0.5, 0.3), ... numbers directly into that formula as degrees
would place vendors ~50+ km apart, not ~0.5 km -- an entirely different,
wrong scenario. The coordinates below convert Phase 5E's original km-
offsets into real (lat, lon) degrees around an illustrative Hyderabad-area
base point (17.45N, 78.47E), verified to reproduce the SAME centroid
distances Phase 5E's report already stated (G1~0.93km, G2~0.57km,
G3~0.35km, G4~0.51km, G_all~1.05km, all confirmed via an independent
Python computation before this file was written) -- Phase 5E's numbers
are unchanged; only this test's coordinate representation is corrected.

SCOPE NOTE: this test file evaluates each candidate INDIVIDUALLY, via the
single-group Decision Engine. It does NOT test overlap resolution (which
candidate is finally SELECTED among G1/G2/G3/G4/G_all) or the pool-superset
search that would confirm/downgrade a WAIT_OR_EXPAND_GROUP result -- both
are Phase 6C's group-formation scope, not Phase 6A's. See
backend/services/decision_engine.py's module docstring for the exact
boundary.
"""

import pytest

from backend.models.contracts import (
    CandidateGroup,
    CommodityParams,
    ConfigParams,
    ProcurementContext,
    TaggedLocation,
    TaggedPrice,
    TransportTier,
    VendorInput,
)
from backend.models.enums import DecisionState, PriceGeographicLevel, VendorLocationStatus
from backend.services.decision_engine import evaluate_group


def _vendor(vendor_id, q, p_ind, lat, lon, h=5):
    return VendorInput(
        vendor_id=vendor_id,
        location=TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=lat, lon=lon),
        q_i=q,
        estimation_provenance=None,
        individual_price_rs_per_kg=p_ind,
        practical_horizon_days=h,
    )


V1 = _vendor("V1", 10.0, 30.0, 17.45, 78.47)
V2 = _vendor("V2", 8.0, 28.0, 17.4527027027027, 78.47472180675979)
V3 = _vendor("V3", 6.0, 32.0, 17.454504504504502, 78.47944361351959)
V4 = _vendor("V4", 12.0, 29.0, 17.45900900900901, 78.48416542027938)
V7 = _vendor("V7", 4.0, 31.0, 17.445495495495496, 78.47755489081567)

COMMODITY = CommodityParams(commodity_id="potato", freshness_window_days=None, moq_kg=200.0)
CONTEXT = ProcurementContext(
    commodity_id="potato",
    date="2026-illustrative",
    wholesale_price=TaggedPrice(value_rs_per_kg=15.0, geographic_level=PriceGeographicLevel.MANDI_LEVEL),
)
CONFIG = ConfigParams(
    d_max_km=2.0,
    trader_margin=0.10,
    transport_tiers=(TransportTier(capacity_kg=100_000, cost_rs=800.0),),  # single flat tier, this scenario
)


def test_g1_group_wait_or_expand_group():
    group = CandidateGroup(group_id="G1", members=(V1, V2, V3, V4))
    result = evaluate_group(group, COMMODITY, CONTEXT, CONFIG)
    assert result.decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value
    assert result.k_star == 5
    assert result.aggregate_quantity_kg == pytest.approx(180.0)
    assert result.moq_shortfall_kg == pytest.approx(20.0)
    assert result.savings_rs == pytest.approx(1550.0)


def test_g2_group_wait_or_expand_group():
    group = CandidateGroup(group_id="G2", members=(V1, V2, V7))
    result = evaluate_group(group, COMMODITY, CONTEXT, CONFIG)
    assert result.decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value
    assert result.k_star == 5
    assert result.aggregate_quantity_kg == pytest.approx(110.0)
    assert result.savings_rs == pytest.approx(625.0)


def test_g3_group_wait_or_expand_group():
    group = CandidateGroup(group_id="G3", members=(V3, V4))
    result = evaluate_group(group, COMMODITY, CONTEXT, CONFIG)
    assert result.decision_state == DecisionState.WAIT_OR_EXPAND_GROUP.value
    assert result.k_star == 5
    assert result.aggregate_quantity_kg == pytest.approx(90.0)
    assert result.savings_rs == pytest.approx(415.0)


def test_g4_group_do_not_buy_together():
    """Economics never turn positive at any k, independent of MOQ --
    a genuine DO_NOT_BUY_TOGETHER, not a WAIT_OR_EXPAND_GROUP."""
    group = CandidateGroup(group_id="G4", members=(V3, V7))
    result = evaluate_group(group, COMMODITY, CONTEXT, CONFIG)
    assert result.decision_state == DecisionState.DO_NOT_BUY_TOGETHER.value
    assert result.savings_rs == pytest.approx(-45.0)


def test_g_all_group_buy_together_with_correct_allocation():
    group = CandidateGroup(group_id="G_all", members=(V1, V2, V3, V4, V7))
    result = evaluate_group(group, COMMODITY, CONTEXT, CONFIG)
    assert result.decision_state == DecisionState.BUY_TOGETHER.value
    assert result.k_star == 5
    assert result.aggregate_quantity_kg == pytest.approx(200.0)
    assert result.moq_met is True
    assert result.savings_rs == pytest.approx(1840.0)

    allocations = {a.vendor_id: a for a in result.per_vendor_allocation}
    assert allocations["V1"].individual_savings_rs == pytest.approx(475.0)
    assert allocations["V2"].individual_savings_rs == pytest.approx(300.0)
    assert allocations["V3"].individual_savings_rs == pytest.approx(345.0)
    assert allocations["V4"].individual_savings_rs == pytest.approx(510.0)
    assert allocations["V7"].individual_savings_rs == pytest.approx(210.0)

    # Per-vendor savings must sum to exactly the group's total savings
    # (Phase 5D Section 4 -- allocation redistributes, never manufactures).
    total_individual_savings = sum(a.individual_savings_rs for a in result.per_vendor_allocation)
    assert total_individual_savings == pytest.approx(result.savings_rs)

    # Per-vendor consumption time equals k* exactly (Phase 5D Section 6).
    for a in result.per_vendor_allocation:
        assert a.consumption_time_days == 5
