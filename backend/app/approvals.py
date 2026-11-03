
import json
import os
import secrets
import tempfile
import threading

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .audit import write_audit_event


DATA_DIR = Path(
    os.getenv("SECUREAI_DATA_DIR")
    or Path(__file__).resolve().parents[2]
)

APPROVALS_FILE = DATA_DIR / "approvals.json"

APPROVAL_TTL = timedelta(
    seconds=int(os.getenv("SECUREAI_APPROVAL_TTL_SECONDS", "3600"))
)

MAX_PENDING = int(os.getenv("SECUREAI_MAX_PENDING", "50"))

if APPROVAL_TTL.total_seconds() <= 0:
    raise ValueError("Approval TTL must be greater than zero")

if MAX_PENDING <= 0:
    raise ValueError("Maximum pending approvals must be greater than zero")


_LOCK = threading.RLock()


class ApprovalLimitError(RuntimeError):
    """Raised when too many approval requests are pending."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(request: dict) -> bool:
    expires_at = request.get("expires_at")

    if not expires_at:
        return True

    try:
        expiry = datetime.fromisoformat(expires_at)

        # Reject timestamps without timezone information.
        if expiry.tzinfo is None:
            return True

        return _now() >= expiry

    except (ValueError, TypeError):
        return True


def _load_approvals() -> dict[str, dict]:
    if not APPROVALS_FILE.exists():
        return {}

    try:
        with APPROVALS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Approval data must be a JSON object")

        for approval_id, request in data.items():
            if not isinstance(request, dict):
                raise ValueError("Invalid approval record")

            if not isinstance(request.get("action"), str):
                raise ValueError("Invalid approval action")

            if request.get("status") not in {
                "pending",
                "approved",
                "rejected",
                "expired",
                "consumed",
            }:
                raise ValueError("Invalid approval status")

        return data

    except (json.JSONDecodeError, OSError, ValueError) as error:
        raise RuntimeError(
            "Could not safely load approval data"
        ) from error


def _save_approvals(approvals: dict[str, dict]) -> None:
    APPROVALS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=APPROVALS_FILE.parent,
            prefix="approvals_",
            suffix=".tmp",
            delete=False,
        ) as file:

            temp_path = Path(file.name)

            json.dump(
                approvals,
                file,
                indent=2,
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, APPROVALS_FILE)

    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def create_approval_request(action: str) -> dict:
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Action must be a non-empty string")

    with _LOCK:
        approvals = _load_approvals()

        pending = [
            request
            for request in approvals.values()
            if request.get("status") == "pending"
            and not _is_expired(request)
        ]

        # Reuse an existing pending request for the same action.
        for request in pending:
            if request["action"] == action:
                return request.copy()

        if len(pending) >= MAX_PENDING:
            raise ApprovalLimitError(
                "Too many pending approval requests"
            )

        now = _now()
        approval_id = secrets.token_urlsafe(16)

        request = {
            "approval_id": approval_id,
            "action": action,
            "status": "pending",
            "created_at": now.isoformat(),
            "expires_at": (now + APPROVAL_TTL).isoformat(),
        }

        approvals[approval_id] = request

        _save_approvals(approvals)

        return request.copy()


def list_approval_requests(
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:

    if limit < 0:
        raise ValueError("Limit cannot be negative")

    with _LOCK:
        approvals = _load_approvals()

        requests = [
            request.copy()
            for request in approvals.values()
            if status is None or request.get("status") == status
        ]

        requests.sort(
            key=lambda item: item.get("created_at", ""),
            reverse=True,
        )

        return requests[:limit]


def _decide(
    approval_id: str,
    approver_id: str,
    new_status: str,
) -> dict | None:

    if new_status not in {"approved", "rejected"}:
        raise ValueError("Invalid approval decision")

    with _LOCK:
        approvals = _load_approvals()
        request = approvals.get(approval_id)

        if request is None or request.get("status") != "pending":
            return None

        if _is_expired(request):
            request["status"] = "expired"
            request["expired_at"] = _now().isoformat()

            _save_approvals(approvals)

            write_audit_event(
                request["action"],
                "expired",
                f"Approval request {approval_id} expired",
                approval_id=approval_id,
            )

            return None

        now = _now()

        request["status"] = new_status
        request["approver_id"] = approver_id
        request["decided_at"] = now.isoformat()

        if new_status == "approved":
            request["expires_at"] = (
                now + APPROVAL_TTL
            ).isoformat()

        _save_approvals(approvals)

        write_audit_event(
            request["action"],
            new_status,
            f"Approval request {approval_id} {new_status} by {approver_id}",
            approver_id=approver_id,
            approval_id=approval_id,
        )

        return request.copy()


def approve_request(
    approval_id: str,
    approver_id: str,
) -> dict | None:

    return _decide(
        approval_id,
        approver_id,
        "approved",
    )


def reject_request(
    approval_id: str,
    approver_id: str,
) -> dict | None:

    return _decide(
        approval_id,
        approver_id,
        "rejected",
    )


def consume_approval(
    approval_id: str,
    action: str,
) -> bool:
    """Consume an approved request exactly once."""

    with _LOCK:
        approvals = _load_approvals()
        request = approvals.get(approval_id)

        if request is None:
            return False

        if request.get("status") != "approved":
            return False

        if request.get("action") != action:
            return False

        if _is_expired(request):
            request["status"] = "expired"
            request["expired_at"] = _now().isoformat()

            _save_approvals(approvals)

            write_audit_event(
                action,
                "expired",
                f"Approved request {approval_id} expired before execution",
                approver_id=request.get("approver_id"),
                approval_id=approval_id,
            )

            return False

        request["status"] = "consumed"
        request["consumed_at"] = _now().isoformat()

        _save_approvals(approvals)

        return True


def get_approval_request(
    approval_id: str,
) -> dict | None:

    with _LOCK:
        approvals = _load_approvals()
        request = approvals.get(approval_id)

        if request is None:
            return None

        return request.copy()
