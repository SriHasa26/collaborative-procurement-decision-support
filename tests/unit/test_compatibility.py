"""
Phase 6C pairwise-compatibility tests -- TEST 1, 2, 3, plus defensive
misuse edge cases.
"""

import pytest

from backend.core import geo_math
from backend.services.compatibility import (
    VendorContractViolation,
    are_geographically_compatible,
    build_compatibility_graph,
)
from backend.models.contracts import TaggedLocation, VendorInput
from backend.models.enums import VendorLocationStatus
from tests.fixtures import group_formation_fixtures as F


# --- TEST 1: exact compatible pair ---
def test_1_exact_compatible_pair_has_edge():
    assert are_geographically_compatible(F.T1_A, F.T1_B, F.D_MAX_KM) is True
    graph = build_compatibility_graph([F.T1_A, F.T1_B], F.D_MAX_KM)
    assert graph.has_edge("T1_A", "T1_B")


# --- TEST 2: exact incompatible pair ---
def test_2_exact_incompatible_pair_has_no_edge():
    assert are_geographically_compatible(F.T2_A, F.T2_B, F.D_MAX_KM) is False
    graph = build_compatibility_graph([F.T2_A, F.T2_B], F.D_MAX_KM)
    assert not graph.has_edge("T2_A", "T2_B")


# --- TEST 3: boundary condition, tested at the exact numeric threshold
#     (2 * D_max), independent of geodesic point construction, per the
#     reasoning in this file's own docstring below. ---
def test_3_boundary_condition_is_inclusive_at_exactly_2x_dmax():
    """Phase 2B's rule is distance <= 2*D_max (inclusive). Testing this
    exactly via hand-constructed coordinates would be fragile (floating-
    point geodesic distances rarely land on an exact value) -- instead,
    this test exercises geo_math.is_within_radius directly at the exact
    boundary value, which is the SAME function are_geographically_compatible
    delegates to internally (backend/services/compatibility.py), so the
    boundary behavior is verified precisely, not approximately."""
    two_d_max = 2 * F.D_MAX_KM
    assert geo_math.is_within_radius(two_d_max, two_d_max) is True  # exactly at boundary -> compatible
    assert geo_math.is_within_radius(two_d_max + 0.0001, two_d_max) is False  # just past -> not compatible
    assert geo_math.is_within_radius(two_d_max - 0.0001, two_d_max) is True  # just under -> compatible


def test_2x_dmax_factor_is_exact_not_dmax_alone():
    """Explicit regression guard against the Step 5 mistake this phase
    warns about: the threshold must be 2*D_max, never D_max alone."""
    # T1_A/T1_B are ~0.99 km apart -- within D_max (2.0) alone AND within
    # 2*D_max (4.0). Use a pair between 2.0 and 4.0 km to actually
    # distinguish the two thresholds.
    a = VendorInput(
        vendor_id="BOUNDARY_A",
        location=TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.45, lon=78.47),
        q_i=10.0, estimation_provenance=None, individual_price_rs_per_kg=25.0, practical_horizon_days=5,
    )
    # ~3.0 km from a (between D_max=2.0 and 2*D_max=4.0)
    b = VendorInput(
        vendor_id="BOUNDARY_B",
        location=TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE,
                                  lat=17.45, lon=78.49833084),
        q_i=10.0, estimation_provenance=None, individual_price_rs_per_kg=25.0, practical_horizon_days=5,
    )
    distance = geo_math.haversine_distance((a.location.lat, a.location.lon), (b.location.lat, b.location.lon))
    assert 2.0 < distance < 4.0  # confirms this pair actually distinguishes the two thresholds
    assert are_geographically_compatible(a, b, F.D_MAX_KM) is True  # correct: uses 2*D_max=4.0
    # If the implementation incorrectly used D_max alone (2.0), this same
    # pair would have been marked incompatible -- so this assertion
    # directly proves the factor of 2 is present.


# --- Defensive misuse: duplicate vendor_id ---
def test_edge_duplicate_vendor_id_raises_contract_violation():
    duplicate = VendorInput(
        vendor_id="T1_A",  # same id as F.T1_A
        location=F.T1_B.location,
        q_i=5.0, estimation_provenance=None, individual_price_rs_per_kg=20.0, practical_horizon_days=5,
    )
    with pytest.raises(VendorContractViolation):
        build_compatibility_graph([F.T1_A, duplicate], F.D_MAX_KM)


# --- Defensive misuse: unusable (missing) location reaching Phase 6C directly ---
def test_edge_missing_location_reaching_phase6c_directly_raises():
    bad_vendor = VendorInput(
        vendor_id="BAD_MISSING_LOC",
        location=TaggedLocation(status=VendorLocationStatus.MISSING),
        q_i=5.0, estimation_provenance=None, individual_price_rs_per_kg=20.0, practical_horizon_days=5,
    )
    with pytest.raises(VendorContractViolation):
        build_compatibility_graph([F.T1_A, bad_vendor], F.D_MAX_KM)


# --- Defensive misuse: malformed (out-of-range) coordinate reaching Phase 6C directly ---
def test_edge_malformed_out_of_range_location_raises():
    bad_vendor = VendorInput(
        vendor_id="BAD_MALFORMED_LOC",
        location=TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=999.0, lon=78.47),
        q_i=5.0, estimation_provenance=None, individual_price_rs_per_kg=20.0, practical_horizon_days=5,
    )
    with pytest.raises(VendorContractViolation):
        build_compatibility_graph([F.T1_A, bad_vendor], F.D_MAX_KM)
