"""
Single-group Decision Engine -- evaluates ONE already-formed candidate group
against every Phase 5D constraint and returns one of the four decision states.

Authoritative source: Phase 5D Section 9 (state definitions, fixed
evaluation order); Phase 5D Sections 4-8 (the formulas, all called from
backend/core/decision_math.py and backend/core/geo_math.py -- never
redefined here).

============================================================================
EXPLICIT SCOPE BOUNDARY (documented per this phase's Step 1 instruction:
"if a required rule is ambiguous, STOP and document the ambiguity rather
than inventing logic"):

Phase 5D Section 9 defines WAIT_OR_EXPAND_GROUP purely from a SINGLE
group's own numbers (conditions 2/4 hold; MOQ fails for every feasible k;
savings would be positive at some k if MOQ were met) -- this function
implements exactly that, self-contained.

Phase 5E Section 12 ADDS a further refinement on top: once a group is
flagged WAIT_OR_EXPAND_GROUP, Phase 5E's pipeline searches the vendor
POOL (already-enumerated supersets from Phase 2B's group-generation step)
for one that achieves BUY_TOGETHER, and DOWNGRADES the result to
DO_NOT_BUY_TOGETHER if no such superset exists.

This module implements Phase 5D's base definition only. It does NOT
implement Phase 5E's superset search or downgrade, because that requires
a POOL of candidate groups -- which requires group FORMATION (the
compatibility graph, connected components, subset enumeration), and group
formation is explicitly out of Phase 6A's scope (owned by Phase 6C).

Consequence, stated plainly: a WAIT_OR_EXPAND_GROUP result from this
module is Phase 5D's base-definition result. Phase 6C must apply Phase 5E's
refinement (searching for a resolving superset) as a POST-PROCESSING step
over this module's output before that result is treated as final.
============================================================================
"""

from dataclasses import dataclass
from typing import Optional, Sequence

from backend.core import decision_math, geo_math
from backend.models.contracts import CandidateGroup, ConfigParams, CommodityParams, GroupDecisionResult, PerVendorAllocation, ProcurementContext
from backend.models.enums import DecisionState


def evaluate_group(
    group: CandidateGroup,
    commodity: CommodityParams,
    context: ProcurementContext,
    config: ConfigParams,
) -> GroupDecisionResult:
    """Evaluate one candidate group. Fixed check order per Phase 5D Section 9
    / Phase 5E Section 16: missing data -> geography -> freshness/horizon ->
    MOQ -> economics."""

    # --- 0. Required-input check -> ABSTAIN (Phase 5E Section 4/13) ---
    missing_reasons = []
    for member in group.members:
        if member.q_i is None:
            missing_reasons.append(f"{member.vendor_id}: demand estimate (q_i) unavailable")
        if not member.location.is_usable():
            missing_reasons.append(f"{member.vendor_id}: location unavailable")
        if member.practical_horizon_days is None:
            missing_reasons.append(f"{member.vendor_id}: practical procurement horizon (H_i,c) unavailable")
        if member.individual_price_rs_per_kg is None:
            missing_reasons.append(f"{member.vendor_id}: individual price unavailable")
    if context.wholesale_price is None:
        missing_reasons.append("context: wholesale price (p_wh) unavailable for this date")

    if missing_reasons:
        return GroupDecisionResult(
            group_id=group.group_id,
            decision_state=DecisionState.ABSTAIN.value,
            reason="; ".join(missing_reasons),
        )

    q_values = [m.q_i for m in group.members]
    p_ind_values = [m.individual_price_rs_per_kg for m in group.members]
    locations = [(m.location.lat, m.location.lon) for m in group.members]
    horizons = [m.practical_horizon_days for m in group.members]

    # --- 1. Geographic feasibility (Phase 5D Section 7; Phase 2A Part 17) ---
    centroid_point = geo_math.centroid(locations)
    d_g = geo_math.max_distance_from_centroid(locations, centroid_point)
    within = geo_math.is_within_radius(d_g, config.d_max_km)
    if not within:
        return GroupDecisionResult(
            group_id=group.group_id,
            decision_state=DecisionState.DO_NOT_BUY_TOGETHER.value,
            reason=f"geographic infeasibility: d(G)={d_g:.3f} km exceeds D_max={config.d_max_km} km",
            centroid_distance_km=d_g,
            within_d_max=False,
        )

    # --- 2. Feasible k range (Phase 5D Section 6; Phase 2A Part 19) ---
    k_range = decision_math.feasible_k_range(commodity.freshness_window_days, horizons)
    if len(k_range) == 0:
        return GroupDecisionResult(
            group_id=group.group_id,
            decision_state=DecisionState.ABSTAIN.value,
            reason="feasible order-horizon range is empty (degenerate freshness/horizon bound)",
            centroid_distance_km=d_g,
            within_d_max=True,
        )

    p_eff = decision_math.effective_price(context.wholesale_price.value_rs_per_kg, config.trader_margin)

    # --- 3. Evaluate every candidate k ---
    per_k = {}
    for k in k_range:
        qg = decision_math.aggregate_quantity(q_values, k)
        tc = decision_math.transport_cost_for_quantity(qg, config.transport_tiers)
        c_ind = decision_math.individual_cost_total(q_values, p_ind_values, k)
        c_collab = decision_math.collaborative_cost(qg, p_eff, tc)
        s = decision_math.savings(c_ind, c_collab)
        moq_applicable, moq_met = decision_math.moq_applicable_and_met(qg, commodity.moq_kg)
        per_k[k] = dict(Q=qg, C_ind=c_ind, C_collab=c_collab, S=s,
                        moq_applicable=moq_applicable, moq_met=moq_met)

    # --- 4. BUY_TOGETHER: any k with (MOQ met or inapplicable) and S(k) > 0 ---
    passing_ks = [
        k for k, v in per_k.items()
        if (not v["moq_applicable"] or v["moq_met"]) and v["S"] > 0
    ]
    if passing_ks:
        k_star = max(passing_ks, key=lambda k: per_k[k]["S"])
        v = per_k[k_star]
        allocations = []
        for member, q in zip(group.members, q_values):
            share = decision_math.per_vendor_share(q, k_star, v["Q"], v["C_collab"])
            c_ind_i = k_star * q * member.individual_price_rs_per_kg
            allocations.append(PerVendorAllocation(
                vendor_id=member.vendor_id,
                share_rs=share,
                individual_savings_rs=decision_math.individual_savings(c_ind_i, share),
                consumption_time_days=decision_math.consumption_time_days(k_star),
            ))
        return GroupDecisionResult(
            group_id=group.group_id,
            decision_state=DecisionState.BUY_TOGETHER.value,
            reason=f"feasible at k={k_star} with positive savings",
            k_star=k_star,
            aggregate_quantity_kg=v["Q"],
            moq_applicable=v["moq_applicable"],
            moq_met=v["moq_met"],
            centroid_distance_km=d_g,
            within_d_max=True,
            individual_cost_total_rs=v["C_ind"],
            collaborative_cost_rs=v["C_collab"],
            savings_rs=v["S"],
            per_vendor_allocation=allocations,
        )

    # --- 5. WAIT_OR_EXPAND_GROUP trigger (Phase 5D Section 9, base definition) ---
    moq_ever_applicable = any(v["moq_applicable"] for v in per_k.values())
    moq_fails_everywhere = moq_ever_applicable and all(
        (not v["moq_met"]) for v in per_k.values() if v["moq_applicable"]
    )
    if moq_fails_everywhere:
        best_k = max(per_k, key=lambda k: per_k[k]["S"])
        best = per_k[best_k]
        if best["S"] > 0:
            shortfall = commodity.moq_kg - best["Q"]
            return GroupDecisionResult(
                group_id=group.group_id,
                decision_state=DecisionState.WAIT_OR_EXPAND_GROUP.value,
                reason=(
                    f"MOQ not met at any feasible k (best k={best_k}, Q={best['Q']:.2f} kg, "
                    f"shortfall={shortfall:.2f} kg), but savings would be positive "
                    f"(Rs {best['S']:.2f}) if MOQ were met. NOTE: this is Phase 5D's "
                    f"base-definition result -- Phase 5E's superset-based refinement "
                    f"(which could downgrade this to DO_NOT_BUY_TOGETHER if no pool "
                    f"expansion resolves it) is NOT applied here; it is deferred to "
                    f"Phase 6C, which owns group formation."
                ),
                k_star=best_k,
                aggregate_quantity_kg=best["Q"],
                moq_applicable=True,
                moq_met=False,
                moq_shortfall_kg=shortfall,
                centroid_distance_km=d_g,
                within_d_max=True,
                individual_cost_total_rs=best["C_ind"],
                collaborative_cost_rs=best["C_collab"],
                savings_rs=best["S"],
            )

    # --- 6. DO_NOT_BUY_TOGETHER: no k achieves positive savings, even ignoring MOQ ---
    best_k = max(per_k, key=lambda k: per_k[k]["S"])
    best = per_k[best_k]
    return GroupDecisionResult(
        group_id=group.group_id,
        decision_state=DecisionState.DO_NOT_BUY_TOGETHER.value,
        reason=(
            f"no feasible k achieves positive savings (best k={best_k}, "
            f"savings={best['S']:.2f})"
        ),
        k_star=None,
        aggregate_quantity_kg=best["Q"],
        moq_applicable=best["moq_applicable"],
        moq_met=best["moq_met"],
        centroid_distance_km=d_g,
        within_d_max=True,
        individual_cost_total_rs=best["C_ind"],
        collaborative_cost_rs=best["C_collab"],
        savings_rs=best["S"],
    )
