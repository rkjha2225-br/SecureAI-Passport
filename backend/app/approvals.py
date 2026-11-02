
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from .audit import write_audit_event


APPROVALS_FILE = Path(__file__).resolve().parents[2] / "approvals.json"


def _load_approvals() -> dict[str, dict]:
    if not APPROVALS_FILE.exists():
        return {}

    try:
        with APPROVALS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Approval data must be a JSON object")

        return data

    except (json.JSONDecodeError, OSError, ValueError) as error:
        raise RuntimeError("Could not safely load approval data") from error


def _save_approvals(approvals: dict[str, dict]) -> None:
    with APPROVALS_FILE.open("w", encoding="utf-8") as file:
        json.dump(approvals, file, indent=2)


def create_approval_request(action: str) -> dict:
    approvals = _load_approvals()
    approval_id = secrets.token_urlsafe(16)

    request = {
        "approval_id": approval_id,
        "action": action,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    approvals[approval_id] = request
    _save_approvals(approvals)

    return request.copy()


def list_approval_requests() -> list[dict]:
    approvals = _load_approvals()
    return [request.copy() for request in approvals.values()]




def approve_request(
    approval_id: str,
    approver_id: str,
) -> dict | None:
    approvals = _load_approvals()
    request = approvals.get(approval_id)

    # Only pending requests can be approved.
    if request is None or request["status"] != "pending":
        return None

    # Update the approval record.
    request["status"] = "approved"
    request["approver_id"] = approver_id
    request["decided_at"] = datetime.now(timezone.utc).isoformat()

    # Save the updated record.
    _save_approvals(approvals)

    # Record the decision in the audit log.
    write_audit_event(
        request["action"],
        "approved",
        f"Approval request {approval_id} approved by {approver_id}",
        approver_id=approver_id,
    )

    return request.copy()


def reject_request(
    approval_id: str,
    approver_id: str,
) -> dict | None:
    approvals = _load_approvals()
    request = approvals.get(approval_id)

    # Only pending requests can be rejected.
    if request is None or request["status"] != "pending":
        return None

    # Update the approval record.
    request["status"] = "rejected"
    request["approver_id"] = approver_id
    request["decided_at"] = datetime.now(timezone.utc).isoformat()

    # Save the updated record.
    _save_approvals(approvals)

    # Record the decision in the audit log.
    write_audit_event(
        request["action"],
        "rejected",
        f"Approval request {approval_id} rejected by {approver_id}",
        approver_id=approver_id,
    )

    return request.copy()



def get_approval_request(approval_id: str) -> dict | None:
    approvals = _load_approvals()
    request = approvals.get(approval_id)

    if request is None:
        return None

    return request.copy()
