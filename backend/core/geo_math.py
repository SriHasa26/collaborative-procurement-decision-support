"""
Pure geographic calculation functions.

Authoritative source: Phase 2A Part 17 (centroid-distance geographic
feasibility) and Part 6B of Phase 2B (Haversine, triangle-inequality
pruning result -- cited here for context only, NOT implemented, since
building the compatibility GRAPH over many vendors is Phase 6C's job).

IMPORTANT SCOPE BOUNDARY (Phase 6A Step 7):
  - haversine_distance, centroid, and max_distance_from_centroid ARE
    in scope: they are the pure Stage-2 math Phase 5D's geographic
    feasibility check (d(G) <= D_max) needs, given an ALREADY-FORMED
    group.
  - Building a compatibility graph across an entire vendor pool
    (NetworkX, connected components, the 2*D_max pruning rule) is
    explicitly OUT of scope here -- that is Phase 2B Stage 1 / Phase 6C.

Every function here is pure: no file access, no vendor validation, no
group-formation logic (Phase 6A Step 11, item 6).
"""

import math
from typing import Sequence, Tuple

Coordinate = Tuple[float, float]  # (lat, lon) in decimal degrees

_EARTH_RADIUS_KM = 6371.0


def haversine_distance(a: Coordinate, b: Coordinate) -> float:
    """Great-circle distance between two (lat, lon) points, in km.
    Authoritative source: Phase 2A Part 17 -- straight-line distance, not
    routed road distance, used deliberately (Phase 1B's own finding that
    a distance-based formula is not more accurate here than a flat lookup
    for cost, and that Haversine is an adequate approximation for
    geographic feasibility)."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def centroid(locations: Sequence[Coordinate]) -> Coordinate:
    """Arithmetic-mean centroid of a set of (lat, lon) points.
    Authoritative source: Phase 2A Part 5/17 -- the single collection point
    for a group is its members' centroid, not a geodesic/weighted centroid;
    this simple mean is what Phase 2A's worked examples use."""
    if not locations:
        raise ValueError("centroid() requires at least one location")
    mean_lat = sum(p[0] for p in locations) / len(locations)
    mean_lon = sum(p[1] for p in locations) / len(locations)
    return (mean_lat, mean_lon)


def max_distance_from_centroid(locations: Sequence[Coordinate], centroid_point: Coordinate) -> float:
    """d(G) = max_i Haversine(L_i, centroid(G)).
    Authoritative source: Phase 2A Part 17; Phase 5D Section 7."""
    if not locations:
        raise ValueError("max_distance_from_centroid() requires at least one location")
    return max(haversine_distance(loc, centroid_point) for loc in locations)


def is_within_radius(distance_km: float, d_max_km: float) -> bool:
    """d(G) <= D_max hard constraint (Phase 2A Part 17; Phase 5D Section 7)."""
    return distance_km <= d_max_km
