"""
Candidate group generation engine (Phase 6C).

Authoritative source: Phase 2B Part 15 Steps 0-3 (the exact pipeline);
Phase 5E Sections 3, 5-7 (restatement, commodity/context isolation).

PIPELINE (unchanged from Phase 2B, implemented here for the first time):

    Phase 6B eligible vendors (already one commodity/context, by
    construction of ProcurementContext)
        -> compatibility graph (backend.services.compatibility, reused)
        -> connected components  (candidate pools)
        -> within-pool candidate enumeration: FULL subset enumeration,
           size >= 2 (Phase 2B's V1 default -- NOT maximal cliques,
           NOT greedy, NOT clustering)
        -> CandidateGroupRecord per candidate, with traceability metadata

This module produces STRUCTURAL CANDIDATES ONLY. It does not call
evaluate_group, does not compute cost/savings/MOQ/freshness, and does not
decide BUY_TOGETHER / WAIT_OR_EXPAND_GROUP / DO_NOT_BUY_TOGETHER anywhere
(Phase 6C Step 16). Those determinations belong to Phase 6D (per-candidate
decision evaluation, reusing backend.services.decision_engine.evaluate_group
unmodified) and Phase 6E (overlap resolution / final selection) -- both
explicitly out of scope here, per Phase 5F's own implementation-order
document (reports/phase5f_traceability_and_implementation_plan.md,
Section 4), which places candidate generation strictly before the
Decision Engine's per-candidate evaluation and before overlap resolution.

WAIT_OR_EXPAND_GROUP BOUNDARY (Phase 6C Step 15): this module does not
compute or store any superset/subset relationship beyond what is already
implicit in `source_pool_id` and `pool_vendor_ids`. Phase 6D's WAIT/EXPAND
resolver (Phase 5E Section 12) can determine "is candidate B a superset of
candidate A" by simple set comparison among candidates sharing the same
source_pool_id -- no precomputed relationship is needed, and none is
built here, so as not to prematurely implement any part of that
refinement's decision logic.
"""

import itertools
from typing import Dict, List, Sequence, Tuple

import networkx as nx

from backend.models.contracts import CandidateGroup, VendorInput
from backend.models.group_formation_contracts import (
    CandidateGroupRecord,
    GroupFormationResult,
    PoolDiagnostic,
)
from backend.services import compatibility

# Threshold used ONLY to attach a non-blocking diagnostic note (Phase 6C
# Step 11) -- never to truncate, drop, or change generation behavior.
# Set to Phase 2B Part 5's own explicitly-tabulated reference point
# (n=15 -> 32,752 candidates), an early warning ahead of Part 14's
# observation that pools around ~25+ members start becoming noticeably
# slower to enumerate exhaustively -- not a hard limit, and not a value
# invented for this phase.
LARGE_POOL_WARNING_THRESHOLD = 15

MINIMUM_GROUP_SIZE = 2  # Phase 2B Part 2: a singleton is not a collaboration


def _pool_id(vendor_ids: Sequence[str]) -> str:
    """Deterministic, content-derived pool identifier."""
    return "pool:" + "+".join(sorted(vendor_ids))


def _group_id(vendor_ids: Sequence[str]) -> str:
    """Deterministic, content-derived candidate-group identifier. Because
    this is derived from the SORTED member set, [A,B] and [B,A] always
    produce the identical group_id -- Phase 6C Step 12/Test 12's
    no-duplicate-candidates requirement is satisfied by construction, not
    by a post-hoc de-duplication pass."""
    return "+".join(sorted(vendor_ids))


def _nominal_candidate_count(pool_size: int) -> int:
    """2^m - m - 1, per Phase 2B Part 5 -- the number of non-empty,
    size->=2 subsets of a pool of m vendors."""
    return (2 ** pool_size) - pool_size - 1


def find_compatible_pools(graph: nx.Graph) -> List[List[str]]:
    """Connected components of the compatibility graph, each a candidate
    pool. Deterministic ordering (Phase 6C Step 12): pools are sorted by
    their own sorted-vendor-id tuple, and vendor_ids within each pool are
    sorted."""
    components = [sorted(c) for c in nx.connected_components(graph)]
    components.sort(key=lambda c: tuple(c))
    return components


def enumerate_candidate_groups(pool_vendor_ids: Sequence[str]) -> List[Tuple[str, ...]]:
    """Full subset enumeration of size >= 2 within one pool -- Phase 2B
    Part 15 Step 3's V1 default. NOT maximal cliques, NOT greedy, NOT
    clustering (Phase 6C Step 9). Deterministic: iterates subset sizes in
    increasing order, and within each size, itertools.combinations over
    the already-sorted pool produces a fixed, reproducible sequence."""
    sorted_pool = sorted(pool_vendor_ids)
    subsets = []
    for size in range(MINIMUM_GROUP_SIZE, len(sorted_pool) + 1):
        for combo in itertools.combinations(sorted_pool, size):
            subsets.append(combo)
    return subsets


def form_candidate_groups(
    eligible_vendors: Sequence[VendorInput],
    commodity_id: str,
    context_date: str,
    d_max_km: float,
) -> GroupFormationResult:
    """Top-level Phase 6C entry point.

    eligible_vendors MUST be exactly the eligible-vendor output of Phase
    6B's evaluate_procurement_context for the SAME (commodity_id,
    context_date) -- Phase 6C does not re-validate or re-estimate demand
    (Phase 6C Step 2). commodity_id/context_date are passed explicitly
    (rather than re-derived from vendor data) so that commodity/context
    isolation (Phase 6C Step 3) is enforced by the caller's own contract
    usage -- every vendor in `eligible_vendors` is assumed, by the Phase
    6B boundary this function relies on, to belong to this one
    (commodity, date) context already. This function does not merge
    vendors across commodities; it has no code path that could, since it
    never receives more than one commodity's vendor list at a time."""

    graph = compatibility.build_compatibility_graph(eligible_vendors, d_max_km)
    vendors_by_id: Dict[str, VendorInput] = {v.vendor_id: v for v in eligible_vendors}

    components = find_compatible_pools(graph)

    pools: List[Tuple[str, Tuple[str, ...]]] = []
    singleton_vendor_ids: List[str] = []
    candidate_records: List[CandidateGroupRecord] = []
    diagnostics: List[PoolDiagnostic] = []

    for component in components:
        if len(component) < MINIMUM_GROUP_SIZE:
            # A vendor with no compatible pool-mate -- normal, expected,
            # not an error (Phase 2B Part 2). No candidate group is
            # generated for it.
            singleton_vendor_ids.extend(component)
            continue

        pool_vendor_ids = tuple(sorted(component))
        pool_id = _pool_id(pool_vendor_ids)
        pools.append((pool_id, pool_vendor_ids))

        nominal_count = _nominal_candidate_count(len(pool_vendor_ids))
        diagnostics.append(PoolDiagnostic(
            pool_id=pool_id,
            vendor_count=len(pool_vendor_ids),
            nominal_candidate_count=nominal_count,
            large_pool_warning=len(pool_vendor_ids) >= LARGE_POOL_WARNING_THRESHOLD,
        ))

        for subset in enumerate_candidate_groups(pool_vendor_ids):
            group_id = _group_id(subset)
            members = tuple(vendors_by_id[vid] for vid in subset)  # already sorted, since subset is sorted
            candidate_records.append(CandidateGroupRecord(
                candidate=CandidateGroup(group_id=group_id, members=members),
                commodity_id=commodity_id,
                context_date=context_date,
                source_pool_id=pool_id,
                pool_vendor_ids=pool_vendor_ids,
            ))

    return GroupFormationResult(
        commodity_id=commodity_id,
        context_date=context_date,
        pools=tuple(pools),
        candidate_groups=tuple(candidate_records),
        singleton_vendor_ids=tuple(sorted(singleton_vendor_ids)),
        diagnostics=tuple(diagnostics),
    )
