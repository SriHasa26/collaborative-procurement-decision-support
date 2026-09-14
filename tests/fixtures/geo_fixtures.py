"""
Geographic-status fixtures G1-G4.

SIMULATED ILLUSTRATIVE FIXTURE DATA -- every coordinate below is invented
for testing only and does not represent a real vendor's location.

Authoritative source: reports/phase5g_implementation_fixtures.md, Section 6.

G3 is a labeling-integrity test only: it references the already-closed
Potato/CEDA finding (Hyderabad district-level proxy, confirmed in Phase
3A.5/3A.6/5D Section 4a) as a CONCEPTUAL anchor. It does not load, recompute,
or modify any file under data/raw/ceda/, and no new price value is derived
from that experiment here.
"""

from backend.models.contracts import TaggedLocation, TaggedPrice
from backend.models.enums import PriceGeographicLevel, VendorLocationStatus

# --- G1: Usable, vendor-specific location ---
G1_LOCATION_VA = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.4520, lon=78.4867)
G1_LOCATION_VB = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.4550, lon=78.4900)
G1_D_MAX_KM = 2.0
G1_EXPECTED_COMPATIBLE = True  # distance is well under 2*D_max = 4 km

# --- G2: Same location type as G1; tests label-integrity in output, not math ---
G2_LOCATION_VA = G1_LOCATION_VA  # identical input; this fixture targets the explanation layer

# --- G3: Price geographic-level proxy integrity (conceptual reference only) ---
G3_DISTRICT_PROXY_PRICE = TaggedPrice(
    value_rs_per_kg=1.0,  # placeholder value -- this fixture tests the TAG, not a real price
    geographic_level=PriceGeographicLevel.DISTRICT_LEVEL_PROXY,
)
G3_MANDI_LEVEL_PRICE = TaggedPrice(
    value_rs_per_kg=1.0,
    geographic_level=PriceGeographicLevel.MANDI_LEVEL,
)

# --- G4: Missing critical location -- isolation test ---
G4_LOCATION_VA = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.4520, lon=78.4867)
G4_LOCATION_VB = TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.4550, lon=78.4900)
G4_LOCATION_VC_MISSING = TaggedLocation(status=VendorLocationStatus.MISSING)
