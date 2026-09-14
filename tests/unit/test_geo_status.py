"""
Automated tests for the geographic-status fixtures G1-G4.
Authoritative source: reports/phase5g_fixture_test_mapping.md.
"""

import pytest

from backend.core import geo_math
from backend.models.enums import PriceGeographicLevel, VendorLocationStatus
from tests.fixtures import geo_fixtures as F


def test_g1_usable_location_feeds_compatibility_math():
    a = (F.G1_LOCATION_VA.lat, F.G1_LOCATION_VA.lon)
    b = (F.G1_LOCATION_VB.lat, F.G1_LOCATION_VB.lon)
    distance = geo_math.haversine_distance(a, b)
    # Correction found during verification: the fixture doc's original
    # ~0.43 km was a rough eyeball estimate, not a computed Haversine
    # value. The actual distance between these two coordinates is ~0.484
    # km (independently verified via a standalone computation before this
    # assertion was fixed) -- tolerance, not exact float equality, per
    # the Phase 5G test-mapping requirement.
    assert distance == pytest.approx(0.4835, abs=0.01)
    compatible = geo_math.is_within_radius(distance, 2 * F.G1_D_MAX_KM)
    assert compatible == F.G1_EXPECTED_COMPATIBLE
    # status must be preserved, not silently upgraded
    assert F.G1_LOCATION_VA.status == VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE
    assert F.G1_LOCATION_VA.is_usable() is True


def test_g2_approximate_location_never_rendered_as_precise():
    """Label-integrity test: the status tag itself must never claim more
    precision than VENDOR_SPECIFIC_APPROXIMATE actually means."""
    location = F.G2_LOCATION_VA
    assert location.status == VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE
    # A future Explanation Generator must render this status using
    # non-exact wording. At the data-contract level (Phase 6A's scope),
    # the assertion is that the tag itself is neither silently dropped
    # nor changed to a higher-precision value by merely reading it.
    assert location.status != VendorLocationStatus.LOCALITY_CENTROID_PROXY
    assert location.status != VendorLocationStatus.MISSING


def test_g3_district_level_proxy_remains_distinct_from_mandi_level():
    """This test does not load, modify, or recompute any file under
    data/raw/ceda/ -- it exercises only the TaggedPrice contract, using a
    freshly-labeled fixture record, per Phase 5G's binding rule."""
    proxy_price = F.G3_DISTRICT_PROXY_PRICE
    mandi_price = F.G3_MANDI_LEVEL_PRICE
    assert proxy_price.geographic_level == PriceGeographicLevel.DISTRICT_LEVEL_PROXY
    assert mandi_price.geographic_level == PriceGeographicLevel.MANDI_LEVEL
    assert proxy_price.geographic_level != PriceGeographicLevel.MANDI_LEVEL
    # No code path in this module ever re-tags one as the other.


def test_g4_missing_location_excludes_only_the_affected_vendor():
    """Batch-level isolation test: VC's missing location must not affect
    VA/VB's compatibility evaluation in the same run."""
    va, vb, vc = F.G4_LOCATION_VA, F.G4_LOCATION_VB, F.G4_LOCATION_VC_MISSING

    assert vc.is_usable() is False
    assert vc.status == VendorLocationStatus.MISSING

    # VA and VB remain usable and compatible, exactly as in G1, unaffected
    # by VC's exclusion.
    assert va.is_usable() is True
    assert vb.is_usable() is True
    distance = geo_math.haversine_distance((va.lat, va.lon), (vb.lat, vb.lon))
    assert geo_math.is_within_radius(distance, 4.0) is True
