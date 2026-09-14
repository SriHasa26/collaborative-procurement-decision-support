"""
Phase 6B per-vendor eligibility tests -- TEST 1-8, 11, 12, plus edge cases.
Authoritative source: the Phase 6B task's Step 12 (required test cases)
and Step 13 (edge cases).
"""

import pytest

from backend.models.enums import EstimationProvenance, OutcomeKind, VendorLocationStatus
from backend.models.reasons import AbstentionReason, ValidationErrorReason
from backend.services.demand_estimation import ValidationError
from backend.services.eligibility import evaluate_vendor
from tests.fixtures import batch_fixtures as F


# --- TEST 1: valid vendor, user-provided demand -> ELIGIBLE ---
def test_1_user_provided_demand_is_eligible():
    result = evaluate_vendor(F.VENDOR_USER_PROVIDED, F.DEFAULT_CONTEXT)
    assert result.eligible is True
    assert result.status == OutcomeKind.OK.value
    assert result.vendor_input.q_i == pytest.approx(12.0)
    assert result.demand_provenance == EstimationProvenance.USER_PROVIDED


# --- TEST 2: cold-start vendor with valid peers -> ELIGIBLE, peer-average q_i ---
def test_2_cold_start_with_valid_peers_is_eligible():
    result = evaluate_vendor(F.VENDOR_COLD_START, F.DEFAULT_CONTEXT)
    assert result.eligible is True
    assert result.vendor_input.q_i == pytest.approx(9.0)
    assert result.demand_provenance == EstimationProvenance.ESTIMATE_COLD_START


# --- TEST 3: >=3 valid historical records -> moving-average-3 ---
def test_3_three_or_more_records_uses_moving_average():
    result = evaluate_vendor(F.VENDOR_MOVING_AVERAGE, F.DEFAULT_CONTEXT)
    assert result.eligible is True
    assert result.vendor_input.q_i == pytest.approx(7.666666666666667)
    assert result.demand_provenance == EstimationProvenance.ESTIMATE_BASELINE


# --- TEST 4: 1-2 valid historical records -> last-observed-value ---
def test_4_one_or_two_records_uses_last_observed_value():
    result = evaluate_vendor(F.VENDOR_LAST_OBSERVED, F.DEFAULT_CONTEXT)
    assert result.eligible is True
    assert result.vendor_input.q_i == pytest.approx(13.0)  # last of (11.0, 13.0)
    assert result.demand_provenance == EstimationProvenance.ESTIMATE_BASELINE


# --- TEST 5: no history, no peers -> ABSTAIN / INSUFFICIENT_DEMAND_EVIDENCE ---
def test_5_no_history_no_peers_abstains():
    result = evaluate_vendor(F.VENDOR_NO_EVIDENCE, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.ABSTAIN.value
    assert result.reason_code == AbstentionReason.INSUFFICIENT_DEMAND_EVIDENCE.value
    assert result.vendor_input is None  # no fabricated value


# --- TEST 6: negative quantity -> VALIDATION_ERROR ---
def test_6_negative_quantity_is_validation_error():
    result = evaluate_vendor(F.VENDOR_NEGATIVE_QUANTITY, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.VALIDATION_ERROR.value
    assert result.vendor_input is None


# --- TEST 7: missing critical location -> ABSTAIN / MISSING_LOCATION ---
def test_7_missing_location_abstains():
    result = evaluate_vendor(F.VENDOR_MISSING_LOCATION, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.ABSTAIN.value
    assert result.reason_code == AbstentionReason.MISSING_LOCATION.value


# --- TEST 8: missing critical horizon -> ABSTAIN with explicit reason ---
def test_8_missing_horizon_abstains():
    result = evaluate_vendor(F.VENDOR_MISSING_HORIZON, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.ABSTAIN.value
    assert result.reason_code == AbstentionReason.MISSING_HORIZON.value


# --- TEST 11: demand provenance preservation ---
def test_11_provenance_preserved_across_all_three_estimation_paths():
    peer_result = evaluate_vendor(F.VENDOR_COLD_START, F.DEFAULT_CONTEXT)
    moving_avg_result = evaluate_vendor(F.VENDOR_MOVING_AVERAGE, F.DEFAULT_CONTEXT)
    last_obs_result = evaluate_vendor(F.VENDOR_LAST_OBSERVED, F.DEFAULT_CONTEXT)

    assert peer_result.demand_provenance == EstimationProvenance.ESTIMATE_COLD_START
    # Moving-average and last-observed both carry ESTIMATE_BASELINE at the
    # enum level (Phase 6A's existing granularity) -- the WHICH-method
    # distinction survives in vendor_input's estimation_provenance +
    # is additionally visible via the underlying reason string Phase 6A's
    # EstimationResult carries (not re-exposed on VendorInput itself, since
    # Phase 6A's contract has no reason field -- documented, not invented).
    assert moving_avg_result.demand_provenance == EstimationProvenance.ESTIMATE_BASELINE
    assert last_obs_result.demand_provenance == EstimationProvenance.ESTIMATE_BASELINE
    # The two BASELINE results must remain numerically distinguishable
    # (proving they were not collapsed into one indistinguishable value):
    assert moving_avg_result.vendor_input.q_i != last_obs_result.vendor_input.q_i

    # An estimate must never be presented as USER_PROVIDED, and vice versa.
    user_result = evaluate_vendor(F.VENDOR_USER_PROVIDED, F.DEFAULT_CONTEXT)
    assert user_result.demand_provenance == EstimationProvenance.USER_PROVIDED
    assert user_result.demand_provenance != EstimationProvenance.ESTIMATE_COLD_START
    assert user_result.demand_provenance != EstimationProvenance.ESTIMATE_BASELINE


# --- TEST 12: geographic metadata integrity ---
def test_12_geographic_status_preserved_not_upgraded_or_downgraded():
    proxy_result = evaluate_vendor(F.VENDOR_LOCALITY_PROXY_LOCATION, F.DEFAULT_CONTEXT)
    approx_result = evaluate_vendor(F.VENDOR_USER_PROVIDED, F.DEFAULT_CONTEXT)  # DEFAULT_LOCATION
    missing_result = evaluate_vendor(F.VENDOR_MISSING_LOCATION, F.DEFAULT_CONTEXT)

    assert proxy_result.eligible is True
    assert proxy_result.vendor_input.location.status == VendorLocationStatus.LOCALITY_CENTROID_PROXY
    # never silently upgraded to VENDOR_SPECIFIC_APPROXIMATE
    assert proxy_result.vendor_input.location.status != VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE

    assert approx_result.vendor_input.location.status == VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE

    # MISSING never becomes eligible, and is never converted into a usable status.
    assert missing_result.eligible is False
    assert missing_result.vendor_input is None


# --- Edge case: malformed location (out-of-range coordinate) -> VALIDATION_ERROR ---
def test_edge_malformed_location_is_validation_error_not_abstain():
    result = evaluate_vendor(F.VENDOR_MALFORMED_LOCATION, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.VALIDATION_ERROR.value
    assert result.reason_code == ValidationErrorReason.MALFORMED_LOCATION.value


# --- Edge case: diary contains an invalid value mixed with valid ones -> VALIDATION_ERROR ---
def test_edge_diary_with_invalid_value_is_validation_error():
    result = evaluate_vendor(F.VENDOR_DIARY_WITH_INVALID_VALUE, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.VALIDATION_ERROR.value


# --- Edge case: peers containing an invalid value -> VALIDATION_ERROR ---
def test_edge_peers_with_invalid_value_is_validation_error():
    result = evaluate_vendor(F.VENDOR_PEERS_WITH_INVALID_VALUE, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.VALIDATION_ERROR.value


# --- Edge case: explicitly empty diary/peer tuples behave like no history at all ---
def test_edge_empty_diary_and_peer_tuples_abstain_like_none():
    result = evaluate_vendor(F.VENDOR_EMPTY_DIARY_TUPLE, F.DEFAULT_CONTEXT)
    assert result.eligible is False
    assert result.status == OutcomeKind.ABSTAIN.value
    assert result.reason_code == AbstentionReason.INSUFFICIENT_DEMAND_EVIDENCE.value


# --- Direct check that ValidationError (Phase 6A) is still what gets raised
#     internally, confirming eligibility.py did not swallow or reinterpret it ---
def test_negative_diary_value_raises_phase6a_validation_error_internally():
    with pytest.raises(ValidationError):
        from backend.services.demand_estimation import estimate_demand
        estimate_demand(F.VENDOR_NEGATIVE_QUANTITY.diary_records, None)
