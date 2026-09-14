"""
Pairwise geographic compatibility and the compatibility graph.

Authoritative source: Phase 2B Part 6B (the exact pruning rule and its
proof); Phase 5E Section 5 (restatement, pairwise-vs-group distinction).

============================================================================
CRITICAL DISTINCTION -- read before touching this file:

This module implements the PAIRWISE, NECESSARY-CONDITION rule:

    Compatible(i, j)  <=>  Haversine(L_i, L_j) <= 2 * D_max

This is NOT the same check as Phase 5D's GROUP-LEVEL, SUFFICIENT
feasibility rule (already implemented, unchanged, in
backend/services/decision_engine.py and backend/core/geo_math.py):

    d(G) = max_i Haversine(L_i, centroid(G)) <= D_max

The proof that the pairwise rule is a valid (lossless) NECESSARY
condition for group-level feasibility is the triangle inequality (Phase
2B Part 6B): if a group G is centroid-feasible, then any two of its
members are at most 2*D_max apart. The converse is explicitly FALSE in
general -- Phase 2B's own "chain caveat" (A-B connected, B-C connected,
but A-C > 2*D_max) means a connected component is a candidate POOL, never
a proof that every subset within it is group-level feasible. That
determination is Phase 6D's job (calling the UNCHANGED evaluate_group),
not this module's.

This module therefore NEVER calls geo_math.centroid or
geo_math.max_distance_from_centroid, and never claims to decide group
feasibility. It reuses ONLY geo_math.haversine_distance and
geo_math.is_within_radius -- no second Haversine implementation exists
anywhere in this codebase.
============================================================================
"""

from typing import Sequence

import networkx as nx

from backend.core import geo_math
from backend.models.contracts import VendorInput


class VendorContractViolation(ValueError):
    """Raised when the input to this module violates the contract Phase
    6C assumes (already-eligible VendorInput objects from Phase 6B) --
    e.g. a duplicate vendor_id, or a vendor whose location is not usable.
    This is a defensive, fail-clearly guard for direct misuse (Phase 6C
    Step 2/19) -- it does NOT re-run Phase 6B's eligibility pipeline, does
    not assign ABSTAIN/VALIDATION_ERROR reason codes, and is not a
    substitute for calling Phase 6B first."""


def _assert_valid_eligible_input(vendors: Sequence[VendorInput]) -> None:
    """Fail-clearly guard, per Phase 6C Step 2/19. Does not duplicate
    Phase 6B's eligibility logic -- only checks the two conditions that
    would silently corrupt THIS module's own graph construction if
    violated: a duplicate vendor_id (would collide into one graph node,
    silently losing a vendor), and an unusable location (would make a
    per-vendor Haversine calculation meaningless)."""
    seen = set()
    for v in vendors:
        if v.vendor_id in seen:
            raise VendorContractViolation(
                f"duplicate vendor_id '{v.vendor_id}' in input -- Phase 6C requires "
                f"the already-deduplicated eligible-vendor output of Phase 6B."
            )
        seen.add(v.vendor_id)
        if not v.location.is_usable():
            raise VendorContractViolation(
                f"vendor '{v.vendor_id}' has an unusable location (status="
                f"{v.location.status.value}) -- this vendor should have been "
                f"routed to ABSTAIN by Phase 6B and never reached Phase 6C. "
                f"This is a contract-misuse guard, not a re-run of Phase 6B eligibility."
            )
        # Coordinate-range check reuses the exact numeric range Phase 6B's
        # validation.py already established for "malformed location"
        # (backend/services/validation.py) -- not a new rule invented
        # here. Without this, an out-of-range lat/lon would silently
        # produce a numerically meaningless (not exception-raising)
        # Haversine result rather than failing clearly.
        lat, lon = v.location.lat, v.location.lon
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            raise VendorContractViolation(
                f"vendor '{v.vendor_id}' has an out-of-range coordinate "
                f"(lat={lat}, lon={lon}) -- this is malformed location data "
                f"that should have been caught as a VALIDATION_ERROR by "
                f"Phase 6B and never reached Phase 6C."
            )


def are_geographically_compatible(a: VendorInput, b: VendorInput, d_max_km: float) -> bool:
    """Compatible(i,j) <=> Haversine(L_i, L_j) <= 2 * D_max.
    Authoritative source: Phase 2B Part 6B; Phase 5E Section 5.
    Reuses geo_math.haversine_distance and geo_math.is_within_radius
    exactly -- no new distance calculation is introduced. The factor of
    2 is exact, not an approximation, and must never be changed to 1
    (plain D_max) or replaced with a different threshold (Phase 6C Step 5)."""
    distance_km = geo_math.haversine_distance((a.location.lat, a.location.lon), (b.location.lat, b.location.lon))
    return geo_math.is_within_radius(distance_km, 2.0 * d_max_km)


def build_compatibility_graph(vendors: Sequence[VendorInput], d_max_km: float) -> nx.Graph:
    """Nodes: eligible vendors (by vendor_id). Edges: an edge (i,j) exists
    only when are_geographically_compatible(i,j) is True.

    This is a compatibility graph only -- it is not a routing graph, a
    logistics route, a savings graph, or a social graph (Phase 6C Step 7).
    No edge weight is added; Phase 2B does not require one at this stage.

    Deterministic construction (Phase 6C Step 12): nodes are added in
    vendor_id-sorted order, and pairs are checked in the same sorted
    order, so the resulting graph's node/edge iteration order is stable
    across repeated runs on identical input."""
    _assert_valid_eligible_input(vendors)

    graph = nx.Graph()
    sorted_vendors = sorted(vendors, key=lambda v: v.vendor_id)
    for v in sorted_vendors:
        graph.add_node(v.vendor_id, vendor=v)

    for i, a in enumerate(sorted_vendors):
        for b in sorted_vendors[i + 1:]:
            if are_geographically_compatible(a, b, d_max_km):
                graph.add_edge(a.vendor_id, b.vendor_id)

    return graph
