"""
Phase 6B batch-pipeline tests -- TEST 9, 10, and context-level edge cases
(Step 13).
"""

from backend.models.batch_contracts import VendorSubmission
from backend.models.contracts import ProcurementContext, TaggedLocation
from backend.models.enums import VendorLocationStatus
from backend.models.reasons import ContextValidationReason
from backend.services.pipeline import evaluate_procurement_context
from tests.fixtures import batch_fixtures as F


# --- TEST 9: mixed batch -- A eligible, B abstain, C validation error ---
def test_9_mixed_batch_separates_vendors_into_correct_collections():
    vendors = [F.VENDOR_USER_PROVIDED, F.VENDOR_MISSING_LOCATION, F.VENDOR_NEGATIVE_QUANTITY]
    result = evaluate_procurement_context(F.DEFAULT_CONTEXT, vendors)

    eligible_ids = {v.vendor_id for v in result.eligible_vendors}
    abstained_ids = {v.vendor_id for v in result.abstained_vendors}
    error_ids = {v.vendor_id for v in result.validation_error_vendors}

    assert eligible_ids == {"T1_user_provided"}
    assert abstained_ids == {"T7_missing_location"}
    assert error_ids == {"T6_negative_quantity"}

    # Each vendor appears in EXACTLY one collection, never more than one.
    all_lists = [eligible_ids, abstained_ids, error_ids]
    for i, a in enumerate(all_lists):
        for j, b in enumerate(all_lists):
            if i != j:
                assert a.isdisjoint(b)


# --- TEST 10: one vendor's failure does not block unrelated valid vendors ---
def test_10_one_failing_vendor_does_not_block_others():
    vendors = [
        F.VENDOR_NEGATIVE_QUANTITY,      # fails
        F.VENDOR_USER_PROVIDED,          # valid
        F.VENDOR_MALFORMED_LOCATION,     # fails
        F.VENDOR_COLD_START,             # valid
        F.VENDOR_MISSING_HORIZON,        # abstains
    ]
    result = evaluate_procurement_context(F.DEFAULT_CONTEXT, vendors)

    eligible_ids = {v.vendor_id for v in result.eligible_vendors}
    assert eligible_ids == {"T1_user_provided", "T2_cold_start"}
    # The batch completed and returned a result for every submitted vendor.
    total = len(result.eligible_vendors) + len(result.abstained_vendors) + len(result.validation_error_vendors)
    assert total == len(vendors)


def test_large_mixed_batch_all_vendors_accounted_for():
    """A larger, more realistic mixed batch -- every submitted vendor must
    appear in exactly one output collection, with no silent drops."""
    vendors = [
        F.VENDOR_USER_PROVIDED,
        F.VENDOR_COLD_START,
        F.VENDOR_MOVING_AVERAGE,
        F.VENDOR_LAST_OBSERVED,
        F.VENDOR_NO_EVIDENCE,
        F.VENDOR_NEGATIVE_QUANTITY,
        F.VENDOR_MISSING_LOCATION,
        F.VENDOR_MISSING_HORIZON,
        F.VENDOR_LOCALITY_PROXY_LOCATION,
        F.VENDOR_MALFORMED_LOCATION,
        F.VENDOR_DIARY_WITH_INVALID_VALUE,
        F.VENDOR_PEERS_WITH_INVALID_VALUE,
        F.VENDOR_EMPTY_DIARY_TUPLE,
    ]
    result = evaluate_procurement_context(F.DEFAULT_CONTEXT, vendors)
    total = len(result.eligible_vendors) + len(result.abstained_vendors) + len(result.validation_error_vendors)
    assert total == len(vendors)
    assert {v.vendor_id for v in result.eligible_vendors} == {
        "T1_user_provided", "T2_cold_start", "T3_moving_average", "T4_last_observed", "T12_locality_proxy",
    }
    assert {v.vendor_id for v in result.abstained_vendors} == {
        "T5_no_evidence", "T7_missing_location", "T8_missing_horizon", "EDGE_empty_diary_tuple",
    }
    assert {v.vendor_id for v in result.validation_error_vendors} == {
        "T6_negative_quantity", "EDGE_malformed_location", "EDGE_diary_invalid_value", "EDGE_peers_invalid_value",
    }


# --- Edge case: empty vendor list -> context-level EMPTY_VENDOR_COLLECTION ---
def test_edge_empty_vendor_list_fails_context_validation():
    result = evaluate_procurement_context(F.DEFAULT_CONTEXT, [])
    assert result.context_validation.is_valid is False
    assert ContextValidationReason.EMPTY_VENDOR_COLLECTION.value in result.context_validation.reasons
    # No per-vendor processing was attempted.
    assert result.eligible_vendors == []
    assert result.abstained_vendors == []
    assert result.validation_error_vendors == []


# --- Edge case: missing commodity -> context-level MISSING_COMMODITY ---
def test_edge_missing_commodity_fails_context_validation():
    bad_context = ProcurementContext(commodity_id="", date="2026-09-14", wholesale_price=F.DEFAULT_CONTEXT.wholesale_price)
    result = evaluate_procurement_context(bad_context, [F.VENDOR_USER_PROVIDED])
    assert result.context_validation.is_valid is False
    assert ContextValidationReason.MISSING_COMMODITY.value in result.context_validation.reasons
    assert result.eligible_vendors == []


# --- Edge case: malformed vendor collection (an item with no vendor_id) ---
def test_edge_malformed_vendor_collection_fails_context_validation():
    malformed = VendorSubmission(
        vendor_id="",
        location=TaggedLocation(status=VendorLocationStatus.MISSING),
        individual_price_rs_per_kg=None,
        practical_horizon_days=None,
    )
    result = evaluate_procurement_context(F.DEFAULT_CONTEXT, [F.VENDOR_USER_PROVIDED, malformed])
    assert result.context_validation.is_valid is False
    assert ContextValidationReason.MALFORMED_VENDOR_COLLECTION.value in result.context_validation.reasons
    # The entire batch stops -- even the otherwise-valid vendor is not processed,
    # per Step 2's "do not silently continue with meaningless input."
    assert result.eligible_vendors == []
