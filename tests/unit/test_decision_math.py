"""
Mathematical regression tests -- Phase 5D Section 12, Scenario 1
(5-vendor onion example). This example does not supply vendor coordinates
(d(G)=1.4 km is given directly, not derived), so it is used here to
regression-test the pure COST/SAVINGS math only (aggregate_quantity,
individual_cost_total, collaborative_cost, savings) -- not the full
Decision Engine, which needs coordinates (see test_decision_engine_regression.py,
which uses Phase 5E's worked example instead, for that).

SIMULATED ILLUSTRATIVE FIXTURE DATA -- reproduced exactly from
reports/phase5d_mathematical_decision_model.md, Section 12, Scenario 1.
"""

import pytest

from backend.core.decision_math import (
    aggregate_quantity,
    collaborative_cost,
    effective_price,
    individual_cost_total,
    savings,
    transport_cost_for_quantity,
)
from backend.models.contracts import TransportTier

# Phase 5D Section 12, Scenario 1: 5 vendors, onion, q_i=5 kg/day each,
# p_ind=Rs 62.5/kg, p_wh=Rs 40/kg, m=0. This scenario's own worked example
# used a specific illustrative transport cost of Rs 1150 (a midpoint of the
# small tier's range), which is scenario-scoped here, not a system default.
Q_VALUES = [5.0, 5.0, 5.0, 5.0, 5.0]
P_IND_VALUES = [62.5, 62.5, 62.5, 62.5, 62.5]
P_WH = 40.0
M = 0.0
SCENARIO_TIERS = (TransportTier(capacity_kg=750, cost_rs=1150.0),)  # single tier for this scenario

EXPECTED_TABLE = {
    1: pytest.approx(-587.50),
    2: pytest.approx(-25.00),
    3: pytest.approx(537.50),
    5: pytest.approx(1662.50),
}


@pytest.mark.parametrize("k,expected_savings", EXPECTED_TABLE.items())
def test_phase5d_scenario1_savings_table(k, expected_savings):
    p_eff = effective_price(P_WH, M)
    qg = aggregate_quantity(Q_VALUES, k)
    c_ind = individual_cost_total(Q_VALUES, P_IND_VALUES, k)
    tc = transport_cost_for_quantity(qg, SCENARIO_TIERS)
    c_collab = collaborative_cost(qg, p_eff, tc)
    s = savings(c_ind, c_collab)
    assert s == expected_savings


def test_phase5d_scenario1_aggregate_quantity_at_k5():
    assert aggregate_quantity(Q_VALUES, 5) == pytest.approx(125.0)


def test_phase5d_scenario1_individual_cost_at_k5():
    assert individual_cost_total(Q_VALUES, P_IND_VALUES, 5) == pytest.approx(7812.50)
