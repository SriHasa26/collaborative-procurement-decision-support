"""
Phase 6C group-formation engine tests -- TEST 4-12, plus Step 19 edge cases.
"""

import pytest

from backend.services.compatibility import VendorContractViolation
from backend.services.group_formation import (
    _group_id,
    enumerate_candidate_groups,
    find_compatible_pools,
    form_candidate_groups,
)
from backend.services import compatibility
from tests.fixtures import group_formation_fixtures as F


# --- TEST 4: three-vendor chain -> one connected component, A-C NOT pairwise compatible ---
def test_4_three_vendor_chain_is_one_component_but_a_c_not_pairwise_compatible():
    vendors = [F.CHAIN_A, F.CHAIN_B, F.CHAIN_C]
    graph = compatibility.build_compatibility_graph(vendors, F.D_MAX_KM)
    pools = find_compatible_pools(graph)
    assert len(pools) == 1
    assert pools[0] == ["CHAIN_A", "CHAIN_B", "CHAIN_C"]
    # Explicitly preserve the distinction this test exists to prove:
    assert graph.has_edge("CHAIN_A", "CHAIN_B")
    assert graph.has_edge("CHAIN_B", "CHAIN_C")
    assert not graph.has_edge("CHAIN_A", "CHAIN_C")  # NOT pairwise compatible


# --- TEST 5: two disconnected pools, no cross-pool candidate ---
def test_5_disconnected_pools_produce_two_components_no_cross_pool_candidates():
    vendors = [F.POOL1_A, F.POOL1_B, F.POOL2_A, F.POOL2_B]
    result = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    assert len(result.pools) == 2
    pool_vendor_sets = {frozenset(vids) for _, vids in result.pools}
    assert frozenset({"POOL1_A", "POOL1_B"}) in pool_vendor_sets
    assert frozenset({"POOL2_A", "POOL2_B"}) in pool_vendor_sets
    # No candidate group mixes members from both pools.
    for record in result.candidate_groups:
        member_ids = {m.vendor_id for m in record.candidate.members}
        assert member_ids.issubset({"POOL1_A", "POOL1_B"}) or member_ids.issubset({"POOL2_A", "POOL2_B"})


# --- TEST 6: commodity isolation -- no cross-commodity grouping ---
def test_6_commodity_isolation_tomato_and_potato_never_mixed():
    tomato_result = form_candidate_groups(
        [F.T1_A, F.T1_B], commodity_id="tomato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    potato_result = form_candidate_groups(
        [F.POOL1_A, F.POOL1_B], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    assert tomato_result.commodity_id == "tomato"
    assert potato_result.commodity_id == "potato"
    tomato_vendor_ids = {m.vendor_id for r in tomato_result.candidate_groups for m in r.candidate.members}
    potato_vendor_ids = {m.vendor_id for r in potato_result.candidate_groups for m in r.candidate.members}
    assert tomato_vendor_ids.isdisjoint(potato_vendor_ids)
    for record in tomato_result.candidate_groups:
        assert record.commodity_id == "tomato"
    for record in potato_result.candidate_groups:
        assert record.commodity_id == "potato"


# --- TEST 7: singleton component -- no collaborative candidate group generated ---
def test_7_singleton_vendor_produces_no_candidate_group():
    vendors = [F.CHAIN_A, F.CHAIN_B, F.CHAIN_C, F.SINGLETON]
    result = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    assert "SINGLETON" in result.singleton_vendor_ids
    for record in result.candidate_groups:
        member_ids = {m.vendor_id for m in record.candidate.members}
        assert "SINGLETON" not in member_ids


# --- TEST 8: candidate enumeration -- exact expected subsets, NOT clique-based ---
def test_8_candidate_enumeration_includes_non_clique_subsets():
    """The chain A-B-C has only 2 direct edges (A-B, B-C), not a
    triangle/clique -- yet Phase 2B's V1 default is FULL subset
    enumeration within the connected component, so {A,C} and {A,B,C}
    must BOTH be generated even though A-C is not a direct edge."""
    pool = ["CHAIN_A", "CHAIN_B", "CHAIN_C"]
    subsets = enumerate_candidate_groups(pool)
    expected = {
        ("CHAIN_A", "CHAIN_B"),
        ("CHAIN_A", "CHAIN_C"),  # NOT a clique edge, but still enumerated
        ("CHAIN_B", "CHAIN_C"),
        ("CHAIN_A", "CHAIN_B", "CHAIN_C"),
    }
    assert set(subsets) == expected
    assert len(subsets) == 4  # 2^3 - 3 - 1 = 4, per Phase 2B Part 5

    result = form_candidate_groups(
        [F.CHAIN_A, F.CHAIN_B, F.CHAIN_C], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    generated_ids = {r.candidate.group_id for r in result.candidate_groups}
    assert generated_ids == {"CHAIN_A+CHAIN_B", "CHAIN_A+CHAIN_C", "CHAIN_B+CHAIN_C", "CHAIN_A+CHAIN_B+CHAIN_C"}


# --- TEST 9: determinism -- identical input produces identical, stably-ordered output ---
def test_9_determinism_across_repeated_runs():
    vendors = [F.CHAIN_C, F.CHAIN_A, F.CHAIN_B]  # deliberately out-of-order input
    result_1 = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    result_2 = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)

    ids_1 = [r.candidate.group_id for r in result_1.candidate_groups]
    ids_2 = [r.candidate.group_id for r in result_2.candidate_groups]
    assert ids_1 == ids_2  # same order, not just same set
    assert result_1.pools == result_2.pools


# --- TEST 10: eligibility boundary -- direct misuse fails clearly, no silent re-run of Phase 6B ---
def test_10_ineligible_vendor_reaching_phase6c_directly_fails_clearly():
    from backend.models.contracts import TaggedLocation, VendorInput
    from backend.models.enums import VendorLocationStatus

    ineligible = VendorInput(
        vendor_id="SHOULD_NOT_HAVE_PASSED",
        location=TaggedLocation(status=VendorLocationStatus.MISSING),  # never should have passed Phase 6B
        q_i=None, estimation_provenance=None, individual_price_rs_per_kg=None, practical_horizon_days=None,
    )
    with pytest.raises(VendorContractViolation):
        form_candidate_groups(
            [F.T1_A, ineligible], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
        )
    # The normal path (only the genuinely eligible vendor) still works correctly on its own.
    normal_result = form_candidate_groups(
        [F.T1_A, F.T1_B], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    assert len(normal_result.candidate_groups) == 1


# --- TEST 11: Phase 5E Section 15 worked example -- structural reproduction ---
def test_11_phase5e_worked_example_structural_relationships():
    """Reproduces the geographic STRUCTURE of Phase 5E's worked example
    (one 5-vendor pool {V1,V2,V3,V4,V7}, V5 isolated) -- does not touch
    or recompute Phase 5E's cost/savings mathematics, which remain
    exclusively Phase 6D's concern via the unmodified evaluate_group."""
    vendors = [F.V1, F.V2, F.V3, F.V4, F.V7, F.V5]
    result = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)

    assert len(result.pools) == 1
    pool_id, pool_vendor_ids = result.pools[0]
    assert set(pool_vendor_ids) == {"V1", "V2", "V3", "V4", "V7"}
    assert "V5" in result.singleton_vendor_ids

    # The full pool's candidate (the group Phase 5D/5E's example found
    # BUY_TOGETHER) must be among the generated candidates -- generation
    # does not decide BUY_TOGETHER here, it only makes the candidate
    # available for Phase 6D to evaluate.
    generated_ids = {r.candidate.group_id for r in result.candidate_groups}
    assert "V1+V2+V3+V4+V7" in generated_ids
    # Nominal count for a 5-vendor pool: 2^5 - 5 - 1 = 26
    assert len(result.candidate_groups) == 26


# --- TEST 12: no duplicate candidates -- [A,B] never separately appears as [B,A] ---
def test_12_no_duplicate_candidates_regardless_of_input_order():
    assert _group_id(["A", "B"]) == _group_id(["B", "A"])

    forward = form_candidate_groups(
        [F.T1_A, F.T1_B], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    backward = form_candidate_groups(
        [F.T1_B, F.T1_A], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    assert len(forward.candidate_groups) == 1
    assert forward.candidate_groups[0].candidate.group_id == backward.candidate_groups[0].candidate.group_id

    # General uniqueness check over a larger pool.
    result = form_candidate_groups(
        [F.V1, F.V2, F.V3, F.V4, F.V7], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    all_ids = [r.candidate.group_id for r in result.candidate_groups]
    assert len(all_ids) == len(set(all_ids))


# ============================ Step 19 edge cases ============================

def test_edge_empty_eligible_collection():
    result = form_candidate_groups([], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    assert result.pools == ()
    assert result.candidate_groups == ()
    assert result.singleton_vendor_ids == ()


def test_edge_one_eligible_vendor_is_a_singleton():
    result = form_candidate_groups([F.T1_A], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    assert result.candidate_groups == ()
    assert result.singleton_vendor_ids == ("T1_A",)


def test_edge_all_vendors_mutually_incompatible():
    vendors = [F.T1_A, F.T2_B, F.SINGLETON]  # each pair far apart from each other
    result = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    assert result.candidate_groups == ()
    assert set(result.singleton_vendor_ids) == {"T1_A", "T2_B", "SINGLETON"}


def test_edge_all_vendors_in_one_pool():
    vendors = [F.POOL1_A, F.POOL1_B]  # both mutually compatible
    result = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    assert len(result.pools) == 1
    assert len(result.candidate_groups) == 1  # 2^2 - 2 - 1 = 1
    assert result.singleton_vendor_ids == ()


def test_large_pool_triggers_non_blocking_diagnostic_without_dropping_anyone():
    """Builds a pool of 15 mutually-compatible vendors (a fully-connected
    clique, all within the 4km threshold of each other) to trigger the
    LARGE_POOL_WARNING_THRESHOLD diagnostic -- confirms it is a warning
    only, never a truncation. 15 is Phase 2B Part 5's own tabulated
    reference point (2^15 - 15 - 1 = 32,752 candidates) -- large enough
    to genuinely exercise the warning path, small enough to keep this
    test fast (well under a second)."""
    from backend.models.contracts import TaggedLocation, VendorInput
    from backend.models.enums import VendorLocationStatus

    base_lat, base_lon = 17.45, 78.47
    n = 15
    vendors = []
    for i in range(n):
        # Tiny offsets (<< 4km apart) so all n are mutually compatible.
        vendors.append(VendorInput(
            vendor_id=f"BIG_{i:02d}",
            location=TaggedLocation(
                status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE,
                lat=base_lat + i * 0.0005, lon=base_lon,
            ),
            q_i=5.0, estimation_provenance=None, individual_price_rs_per_kg=20.0, practical_horizon_days=5,
        ))
    result = form_candidate_groups(vendors, commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM)
    assert len(result.pools) == 1
    assert result.diagnostics[0].large_pool_warning is True
    assert result.diagnostics[0].vendor_count == n
    assert result.diagnostics[0].nominal_candidate_count == (2 ** n - n - 1)
    # No vendor was dropped and no candidate was truncated.
    all_member_ids = {m.vendor_id for r in result.candidate_groups for m in r.candidate.members}
    assert all_member_ids == {f"BIG_{i:02d}" for i in range(n)}
    assert len(result.candidate_groups) == (2 ** n - n - 1)


def test_small_pool_does_not_trigger_large_pool_warning():
    result = form_candidate_groups(
        [F.CHAIN_A, F.CHAIN_B, F.CHAIN_C], commodity_id="potato", context_date="2026-09-14", d_max_km=F.D_MAX_KM
    )
    assert result.diagnostics[0].large_pool_warning is False
