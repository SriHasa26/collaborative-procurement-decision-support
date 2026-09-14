"""
Automated tests for the demand-estimation fixtures D1-D4.
Authoritative source: reports/phase5g_fixture_test_mapping.md.
"""

import pytest

from backend.models.enums import EstimationProvenance, OutcomeKind
from backend.services.demand_estimation import (
    ValidationError,
    cold_start_estimate,
    estimate_demand,
    limited_history_estimate,
)
from tests.fixtures import demand_fixtures as F


def test_d1_cold_start_with_valid_peers():
    result = cold_start_estimate(F.D1_PEER_Q_VALUES)
    assert result.outcome == OutcomeKind.OK
    assert result.q_i == pytest.approx(F.D1_EXPECTED_Q_I)
    assert result.provenance == EstimationProvenance.ESTIMATE_COLD_START


def test_d2_limited_history_uses_moving_average_not_last_observed():
    result = limited_history_estimate(F.D2_DIARY_RECORDS)
    assert result.outcome == OutcomeKind.OK
    assert result.q_i == pytest.approx(F.D2_EXPECTED_Q_I, rel=1e-9)
    # Negative assertion (Phase 5G test-mapping requirement): must NOT equal
    # the last-observed-value, which would indicate the wrong method ran.
    assert result.q_i != pytest.approx(F.D2_LAST_OBSERVED_VALUE_WOULD_BE)
    assert result.provenance == EstimationProvenance.ESTIMATE_BASELINE


def test_d3_insufficient_evidence_abstains_without_fabricating():
    result = estimate_demand(F.D3_DIARY_RECORDS, F.D3_PEER_Q_VALUES)
    assert result.outcome == OutcomeKind.ABSTAIN
    assert result.q_i is None  # no fabricated value
    assert result.provenance is None


def test_d4_negative_quantity_is_validation_error_not_abstain():
    with pytest.raises(ValidationError):
        estimate_demand(F.D4_INVALID_DIARY_RECORDS, peer_q_values=None)


def test_d3_and_d4_are_distinguishable_outcomes():
    """D3 (well-formed, empty) must not be confused with D4 (malformed).
    D3 returns a normal EstimationResult with outcome=ABSTAIN; D4 raises
    an exception instead of returning any result at all."""
    d3_result = estimate_demand(F.D3_DIARY_RECORDS, F.D3_PEER_Q_VALUES)
    assert d3_result.outcome == OutcomeKind.ABSTAIN
    with pytest.raises(ValidationError):
        estimate_demand(F.D4_INVALID_DIARY_RECORDS, peer_q_values=None)
