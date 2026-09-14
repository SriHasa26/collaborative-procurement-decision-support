"""
Pure mathematical functions from Phase 5D (the authoritative decision model),
which itself preserves Phase 2A's original formulas unchanged.

Every function here is PURE: given the same inputs, always the same output,
no file/database/network access, no vendor validation, no group formation.
(Phase 6A Step 5/11.) Each docstring cites the exact Phase 5D section the
formula comes from -- nothing here is invented from a function name.

Notation follows Phase 5D Section 2 exactly:
  q_i          -- demand estimate, kg/day
  k            -- order horizon, days
  Q_G(k)       -- aggregate group quantity, kg
  p_ind_i,c    -- vendor i's individual price, Rs/kg
  p_wh_c,t     -- wholesale price, Rs/kg
  m            -- trader margin (ratio)
  p_eff_c,t    -- effective price = p_wh_c,t * (1 + m)
  TC(tier)     -- flat transport charge for a capacity tier, Rs
  F_c          -- freshness window, days (None = does not bind)
  H_i,c        -- vendor i's practical procurement horizon, days
"""

from typing import Optional, Sequence

from backend.models.contracts import TransportTier


def effective_price(p_wh: float, m: float) -> float:
    """p_eff_c,t = p_wh_c,t * (1 + m). Phase 5D Section 2 (parameter table);
    Phase 2A Part 7."""
    return p_wh * (1.0 + m)


def aggregate_quantity(q_values: Sequence[float], k: int) -> float:
    """Q_G(k) = k * sum(q_i for i in G). Phase 5D Section 3."""
    return k * sum(q_values)


def individual_cost_total(q_values: Sequence[float], p_ind_values: Sequence[float], k: int) -> float:
    """C_ind_total,G(k) = sum_i (k * q_i * p_ind_i,c). Phase 5D Section 4A;
    Phase 2A Part 10. q_values and p_ind_values must be aligned by index
    (one entry per vendor)."""
    if len(q_values) != len(p_ind_values):
        raise ValueError("q_values and p_ind_values must have the same length")
    return sum(k * q * p for q, p in zip(q_values, p_ind_values))


def transport_cost_for_quantity(quantity_kg: float, tiers: Sequence[TransportTier]) -> float:
    """TC_G(k) = TC(tier(Q_G(k))). Phase 5D Section 4B; Phase 2A Part 13 --
    a flat, tiered lookup, NOT a distance-based formula (Phase 1B's own
    finding that short intra-city trips are dominated by a near-fixed
    per-trip charge). Tiers must be supplied sorted ascending by capacity;
    the first tier whose capacity_kg >= quantity_kg is used. If quantity
    exceeds every tier's capacity, this is a configuration gap (no tier
    covers the group) and raises ValueError rather than silently picking
    the largest tier or fabricating a cost."""
    for tier in sorted(tiers, key=lambda t: t.capacity_kg):
        if quantity_kg <= tier.capacity_kg:
            return tier.cost_rs
    raise ValueError(
        f"No transport tier covers a quantity of {quantity_kg} kg -- "
        f"configuration gap, not a value to guess at."
    )


def collaborative_cost(quantity_kg: float, p_eff: float, transport_cost_rs: float) -> float:
    """C_collab_G,c(k) = Q_G(k) * p_eff_c,t + TC_G(k). Phase 5D Section 4B;
    Phase 2A Part 11. Handling/wastage costs are deliberately excluded --
    Phase 2A Part 11's own finding that no data exists to populate them;
    a future prototype must introduce such a cost only as an explicit,
    separately-labeled configurable parameter (Phase 5D Section 4), never
    folded in here."""
    return quantity_kg * p_eff + transport_cost_rs


def savings(individual_cost_total_rs: float, collaborative_cost_rs: float) -> float:
    """Savings_G(k) = C_ind_total,G(k) - C_collab_G,c(k). Phase 5D Section 4C;
    Phase 2A Part 15."""
    return individual_cost_total_rs - collaborative_cost_rs


def per_vendor_share(q_i: float, k: int, quantity_kg: float, collaborative_cost_rs: float) -> float:
    """Share_i(k) = (k * q_i / Q_G(k)) * C_collab_G,c(k). Phase 5D Section 4
    (quantity-proportional allocation); Phase 2A Part 14."""
    if quantity_kg == 0:
        raise ValueError("per_vendor_share() undefined when Q_G(k) == 0")
    return (k * q_i / quantity_kg) * collaborative_cost_rs


def individual_savings(individual_cost_i_rs: float, share_rs: float) -> float:
    """IndividualSavings_i(k) = C_ind_i,c(k) - Share_i(k). Phase 5D Section 4."""
    return individual_cost_i_rs - share_rs


def consumption_time_days(k: int) -> int:
    """Per-vendor consumption time under quantity-proportional allocation
    equals k exactly -- a direct, already-implied consequence of Phase 2A's
    own math, not a new assumption. Phase 5D Section 6:
        consumption_time_i = allocated_quantity_i / q_i = (k*q_i)/q_i = k
    """
    return k


def break_even_quantity(transport_cost_small_tier_rs: float, p_ind: float, p_eff: float) -> float:
    """BE_c(t) = TC(small tier) / (p_ind_i,c - p_eff_c,t). Phase 5D Section 5
    references this via Phase 2A Part 16 -- EXPLANATORY ONLY, never an
    independent gate (it restates the same zero-crossing NetSavings already
    checks, expressed in kilograms instead of rupees)."""
    denom = p_ind - p_eff
    if denom <= 0:
        raise ValueError(
            "break_even_quantity() is undefined when p_ind <= p_eff -- "
            "collaboration is not price-favorable at all in this case."
        )
    return transport_cost_small_tier_rs / denom


def feasible_k_range(freshness_window_days: Optional[int], horizon_days: Sequence[Optional[int]]) -> range:
    """k in {1, ..., floor(min(F_c, min_i H_i,c))}. Phase 5D Section 6;
    Phase 2A Part 19. freshness_window_days=None means F_c does not bind
    (e.g. long shelf life). Any None in horizon_days means that vendor's
    H_i,c is undefined -- per Phase 2A Part 31 / Phase 5E Section 4, this
    is an eligibility failure (ABSTAIN), not something this pure function
    silently works around; it raises so the caller (the Decision Engine)
    can route to ABSTAIN explicitly."""
    if any(h is None for h in horizon_days):
        raise ValueError(
            "feasible_k_range() requires every vendor's H_i,c to be defined -- "
            "an undefined horizon is an eligibility failure (ABSTAIN), not "
            "a value this function may substitute for."
        )
    if not horizon_days:
        raise ValueError("feasible_k_range() requires at least one vendor's H_i,c")
    bound_candidates = [h for h in horizon_days]
    if freshness_window_days is not None:
        bound_candidates.append(freshness_window_days)
    bound = min(bound_candidates)
    return range(1, int(bound) + 1)


def moq_applicable_and_met(quantity_kg: float, moq_kg: Optional[float]) -> tuple:
    """Procurement quantity constraint: Q_G(k) >= MOQ_c, applied ONLY if
    MOQ_c is known. Phase 5D Section 5; Phase 2A Part 18 -- no substitute
    value is ever used when MOQ_c is absent. Returns (applicable, met)
    where met is None when not applicable."""
    if moq_kg is None:
        return False, None
    return True, quantity_kg >= moq_kg
