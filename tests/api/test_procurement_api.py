"""
Phase 6F tests: the FastAPI HTTP boundary (backend/api/).

Every test goes through the real HTTP layer via FastAPI's TestClient --
none manually invokes a route function or an internal Phase 6B/6C/6D/6E
function directly. This is deliberate: Phase 6F's own requirement is that
the API be exercised as HTTP -> FastAPI -> ProcurementRunService.run() ->
pipeline -> HTTP response, never bypassed.

Covers required test cases T1-T10 (numbering per the Phase 6F task spec).
"""

from fastapi.testclient import TestClient

from backend.api.main import app
from tests.fixtures.api_fixtures import (
    ABSTAIN_NO_EVIDENCE,
    ELIGIBLE_1,
    ELIGIBLE_2,
    ELIGIBLE_3,
    FAR_A,
    FAR_B,
    LOW_PRICE_1,
    LOW_PRICE_2,
    VALIDATION_ERROR_NEGATIVE_QTY,
    build_request_payload,
)

client = TestClient(app)


# --- T1: health check ---
def test_t1_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- T2: full procurement analysis ---
def test_t2_full_procurement_analysis():
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["run_status"] == "COMPLETED"
    # Input summary
    assert body["total_vendors_submitted"] == 3
    assert body["eligible_vendor_count"] == 3
    # Vendor outcomes
    eligible_ids = {v["vendor_id"] for v in body["batch_eligibility"]["eligible_vendors"]}
    assert eligible_ids == {"ELIGIBLE_1", "ELIGIBLE_2", "ELIGIBLE_3"}
    # Group formation
    assert body["group_formation"] is not None
    assert len(body["group_formation"]["candidate_groups"]) > 0
    # Group decisions
    assert len(body["final_selection"]["all_evaluated_results"]) > 0
    # Final selection
    assert len(body["final_selection"]["selected_group_ids"]) >= 1
    assert body["final_selection"]["total_savings_rs"] > 0


# --- T3: mixed vendor outcomes ---
def test_t3_mixed_vendor_outcomes():
    payload = build_request_payload(
        [ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3, ABSTAIN_NO_EVIDENCE, VALIDATION_ERROR_NEGATIVE_QTY]
    )
    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["eligible_vendor_count"] == 3
    assert body["abstained_vendor_count"] == 1
    assert body["validation_error_vendor_count"] == 1
    assert body["run_status"] == "COMPLETED_WITH_ABSTENTIONS"

    abstained_ids = {v["vendor_id"] for v in body["batch_eligibility"]["abstained_vendors"]}
    error_ids = {v["vendor_id"] for v in body["batch_eligibility"]["validation_error_vendors"]}
    assert abstained_ids == {"ABSTAIN_NO_EVIDENCE"}
    assert error_ids == {"VALIDATION_ERROR_NEGATIVE_QTY"}


# --- T4: zero eligible vendors ---
def test_t4_zero_eligible_vendors():
    payload = build_request_payload([ABSTAIN_NO_EVIDENCE, VALIDATION_ERROR_NEGATIVE_QTY])
    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["eligible_vendor_count"] == 0
    assert body["group_formation"] is None
    assert body["final_selection"] is None
    assert body["run_status"] == "COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS"


# --- T5: one eligible vendor ---
def test_t5_one_eligible_vendor():
    payload = build_request_payload([ELIGIBLE_1])
    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["eligible_vendor_count"] == 1
    assert body["group_formation"] is None
    assert body["run_status"] == "COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS"


# --- T6: no compatible groups ---
def test_t6_no_compatible_groups():
    payload = build_request_payload([FAR_A, FAR_B])
    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["eligible_vendor_count"] == 2
    assert body["group_formation"] is not None
    assert body["candidate_group_count"] == 0
    assert body["final_selection"] is None
    assert body["run_status"] == "COMPLETED_NO_GROUPS"


def test_candidates_exist_but_none_selected():
    payload = build_request_payload([LOW_PRICE_1, LOW_PRICE_2])
    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["candidate_group_count"] > 0
    assert body["final_selection"]["selected_group_ids"] == []
    assert body["run_status"] == "COMPLETED_NO_SELECTION"


# --- T7: malformed API request ---
def test_t7_malformed_request_missing_required_field():
    # Missing "commodity" entirely -- a structural/schema error, not a
    # domain-data error.
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2])
    del payload["commodity"]

    response = client.post("/procurement/analyze", json=payload)
    assert response.status_code == 422


def test_t7_malformed_request_wrong_type():
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2])
    payload["vendor_submissions"] = "not-a-list"

    response = client.post("/procurement/analyze", json=payload)
    assert response.status_code == 422


def test_t7_malformed_request_not_json():
    response = client.post(
        "/procurement/analyze", content=b"{not valid json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 422


# --- T8: JSON serialization ---
def test_t8_json_serialization_has_no_python_object_leakage():
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    response = client.post("/procurement/analyze", json=payload)
    assert response.status_code == 200

    body = response.json()  # already proves it is valid JSON

    suspicious_markers = (" object at 0x", "Enum", "DecisionState.", "OutcomeKind.", "<class ")

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                assert isinstance(k, str)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            for marker in suspicious_markers:
                assert marker not in node, f"leaked Python representation: {node!r}"
        else:
            assert node is None or isinstance(node, (int, float, bool))

    walk(body)

    # Spot-check specific fields are plain, clean strings (Enum -> .value).
    first_group = body["final_selection"]["all_evaluated_results"][0]
    assert first_group["decision"]["decision_state"] in {
        "BUY_TOGETHER", "WAIT_OR_EXPAND_GROUP", "DO_NOT_BUY_TOGETHER", "ABSTAIN",
    }
    assert first_group["final_decision_state"] in {
        "BUY_TOGETHER", "WAIT_OR_EXPAND_GROUP", "DO_NOT_BUY_TOGETHER", "ABSTAIN",
    }


# --- T9: deterministic response structure ---
def test_t9_deterministic_response_across_repeated_requests():
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3, ABSTAIN_NO_EVIDENCE])

    first = client.post("/procurement/analyze", json=payload).json()
    second = client.post("/procurement/analyze", json=payload).json()

    assert first == second


# --- T17 (spec Section 17): explicit end-to-end HTTP integration test ---
def test_full_http_to_pipeline_integration():
    """HTTP request -> FastAPI -> ProcurementRunService.run() -> full
    Phase 6B-6D pipeline -> HTTP response, exercised purely through the
    public HTTP interface (no internal function called directly)."""
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["commodity_id"] == "tomato"
    assert body["run_status"] == "COMPLETED"
    assert body["final_selection"]["selected_group_ids"]
    assert body["final_selection"]["total_savings_rs"] > 0
