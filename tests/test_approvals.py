
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend"),
)

from app.approvals import (
    approve_request,
    create_approval_request,
    reject_request,
)
from app.audit import read_audit_events


def test_approval_request_starts_pending():
    request = create_approval_request("delete_customer_records")

    assert request["status"] == "pending"


def test_pending_request_can_be_approved():
    request = create_approval_request("delete_customer_records")

    result = approve_request(
        request["approval_id"],
        "approver-001",
    )

    assert result["status"] == "approved"
    assert result["approver_id"] == "approver-001"


def test_pending_request_can_be_rejected():
    request = create_approval_request("delete_customer_records")

    result = reject_request(
        request["approval_id"],
        "approver-001",
    )

    assert result["status"] == "rejected"
    assert result["approver_id"] == "approver-001"


def test_request_cannot_be_decided_twice():
    request = create_approval_request("delete_customer_records")
    approval_id = request["approval_id"]

    approve_request(approval_id, "approver-001")
    result = reject_request(approval_id, "approver-001")

    assert result is None


def test_unknown_approval_id_is_not_approved():
    result = approve_request(
        "unknown-approval-id",
        "approver-001",
    )

    assert result is None


def test_approval_decision_is_written_to_audit_log():
    request = create_approval_request("delete_customer_records")

    result = approve_request(
        request["approval_id"],
        "approver-001",
    )
    events = read_audit_events()

    assert result["status"] == "approved"
    assert any(
        event["status"] == "approved"
        and request["approval_id"] in event["reason"]
        and "approver-001" in event["reason"]
        for event in events
    )


def test_rejection_decision_is_written_to_audit_log():
    request = create_approval_request("delete_customer_records")

    result = reject_request(
        request["approval_id"],
        "approver-001",
    )
    events = read_audit_events()

    assert result["status"] == "rejected"
    assert any(
        event["status"] == "rejected"
        and request["approval_id"] in event["reason"]
        and "approver-001" in event["reason"]
        for event in events
    )


def test_approved_request_does_not_execute_action():
    request = create_approval_request("delete_customer_records")

    result = approve_request(
        request["approval_id"],
        "approver-001",
    )

    assert result["status"] == "approved"
    assert result["action"] == "delete_customer_records"
