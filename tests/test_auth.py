
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend"),
)

os.environ["SECUREAI_API_KEY"] = "test-key-for-automated-tests"
os.environ["SECUREAI_APPROVER_ID"] = "approver-001"

from app.approvals import create_approval_request
from app.main import app

client = TestClient(app)

API_HEADERS = {
    "X-API-Key": "test-key-for-automated-tests",
}

APPROVER_HEADERS = {
    **API_HEADERS,
    "X-Approver-ID": "approver-001",
}


def test_action_without_key_is_rejected():
    response = client.post(
        "/actions/execute",
        json={"action": "read_demo_records"},
    )
    assert response.status_code == 401


def test_action_with_wrong_key_is_rejected():
    response = client.post(
        "/actions/execute",
        json={"action": "read_demo_records"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_action_with_correct_key_executes():
    response = client.post(
        "/actions/execute",
        json={"action": "read_demo_records"},
        headers=API_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "executed"


def test_approval_without_api_key_is_rejected():
    response = client.post("/approvals/test-approval-id/approve")
    assert response.status_code == 401


def test_approval_with_wrong_api_key_is_rejected():
    response = client.post(
        "/approvals/test-approval-id/approve",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_approval_status_endpoint_returns_existing_request():
    request = create_approval_request("delete_customer_records")
    response = client.get(
        f"/approvals/{request['approval_id']}",
        headers=API_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["approval"]["approval_id"] == request["approval_id"]


def test_approval_status_endpoint_returns_404_for_unknown_id():
    response = client.get(
        "/approvals/unknown-approval-id",
        headers=API_HEADERS,
    )
    assert response.status_code == 404


def test_approval_endpoint_rejects_second_decision():
    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    first_response = client.post(
        f"/approvals/{approval_id}/approve",
        headers=APPROVER_HEADERS,
    )
    second_response = client.post(
        f"/approvals/{approval_id}/approve",
        headers=APPROVER_HEADERS,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 404


def test_approval_status_reflects_approved_decision():
    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    decision = client.post(
        f"/approvals/{approval_id}/approve",
        headers=APPROVER_HEADERS,
    )
    response = client.get(
        f"/approvals/{approval_id}",
        headers=API_HEADERS,
    )

    assert decision.status_code == 200
    assert response.status_code == 200
    assert response.json()["approval"]["status"] == "approved"


def test_approval_status_reflects_rejected_decision():
    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    reject_response = client.post(
        f"/approvals/{approval_id}/reject",
        headers=APPROVER_HEADERS,
    )
    status_response = client.get(
        f"/approvals/{approval_id}",
        headers=API_HEADERS,
    )

    assert reject_response.status_code == 200
    assert status_response.status_code == 200
    assert status_response.json()["approval"]["status"] == "rejected"


def test_rejected_request_cannot_be_approved_again():
    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    first_response = client.post(
        f"/approvals/{approval_id}/reject",
        headers=APPROVER_HEADERS,
    )
    second_response = client.post(
        f"/approvals/{approval_id}/approve",
        headers=APPROVER_HEADERS,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 404


def test_rejected_approval_is_recorded_in_audit_log():
    from app.audit import read_audit_events

    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    response = client.post(
        f"/approvals/{approval_id}/reject",
        headers=APPROVER_HEADERS,
    )
    events = read_audit_events()

    assert response.status_code == 200
    assert any(
        event["status"] == "rejected"
        and approval_id in event["reason"]
        for event in events
    )


def test_reject_approval_without_api_key_is_unauthorized():
    request = create_approval_request("delete_customer_records")

    response = client.post(
        f"/approvals/{request['approval_id']}/reject",
    )
    assert response.status_code == 401


def test_reject_approval_with_wrong_api_key_is_unauthorized():
    from app.approvals import get_approval_request

    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    response = client.post(
        f"/approvals/{approval_id}/reject",
        headers={"X-API-Key": "wrong-key"},
    )
    saved_request = get_approval_request(approval_id)

    assert response.status_code == 401
    assert saved_request["status"] == "pending"


def test_approving_unknown_request_returns_404():
    response = client.post(
        "/approvals/nonexistent-id/approve",
        headers=APPROVER_HEADERS,
    )
    assert response.status_code == 404


def test_rejecting_unknown_request_returns_404():
    response = client.post(
        "/approvals/nonexistent-id/reject",
        headers=APPROVER_HEADERS,
    )
    assert response.status_code == 404


def test_unknown_approval_status_returns_404():
    response = client.get(
        "/approvals/nonexistent-id",
        headers=API_HEADERS,
    )
    assert response.status_code == 404


def test_approval_status_requires_authentication():
    response = client.get("/approvals/nonexistent-id")
    assert response.status_code == 401


def test_approval_status_with_wrong_key_is_rejected():
    response = client.get(
        "/approvals/nonexistent-id",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_approved_request_cannot_be_rejected_again():
    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    approved = client.post(
        f"/approvals/{approval_id}/approve",
        headers=APPROVER_HEADERS,
    )
    rejected = client.post(
        f"/approvals/{approval_id}/reject",
        headers=APPROVER_HEADERS,
    )

    assert approved.status_code == 200
    assert rejected.status_code == 404


def test_decision_timestamp_is_saved():
    request = create_approval_request("delete_customer_records")

    response = client.post(
        f"/approvals/{request['approval_id']}/approve",
        headers=APPROVER_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["approval"]["decided_at"] is not None
