
import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path(
    os.getenv("SECUREAI_DATA_DIR")
    or Path(__file__).resolve().parents[2]
)

AUDIT_FILE = DATA_DIR / "audit.log"

GENESIS_HASH = "0" * 64

_LOCK = threading.Lock()


def _digest(prev_hash: str, event: dict) -> str:
    body = json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        (prev_hash + body).encode("utf-8")
    ).hexdigest()


def _last_hash() -> str:
    """Return the latest chained hash, ignoring old unchained records."""

    if not AUDIT_FILE.exists():
        return GENESIS_HASH

    previous_hash = GENESIS_HASH

    with AUDIT_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"Invalid audit log at line {line_number}"
                ) from error

            if not isinstance(event, dict):
                raise RuntimeError(
                    f"Invalid audit record at line {line_number}"
                )

            # Ignore old records that do not have a hash.
            if "hash" not in event:
                continue

            stored_hash = event["hash"]
            event_data = event.copy()
            del event_data["hash"]

            expected_previous = previous_hash

            if event_data.get("prev_hash") != expected_previous:
                raise RuntimeError(
                    f"Audit chain broken at line {line_number}"
                )

            calculated_hash = _digest(
                expected_previous,
                event_data,
            )

            if stored_hash != calculated_hash:
                raise RuntimeError(
                    f"Audit hash mismatch at line {line_number}"
                )

            previous_hash = stored_hash

    return previous_hash


def write_audit_event(
    action: str,
    status: str,
    reason: str,
    approver_id: str | None = None,
    approval_id: str | None = None,
) -> None:

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "status": status,
        "reason": reason,
        "approver_id": approver_id,
    }

    if approval_id is not None:
        event["approval_id"] = approval_id

    with _LOCK:

        AUDIT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        previous_hash = _last_hash()

        event["prev_hash"] = previous_hash

        event["hash"] = _digest(
            previous_hash,
            event.copy(),
        )

        with AUDIT_FILE.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as file:

            file.write(json.dumps(event) + "\n")
            file.flush()
            os.fsync(file.fileno())


def verify_audit_chain() -> tuple[bool, int | None]:
    """
    Verify the audit hash chain.

    Returns:
        (True, None) if valid.
        (False, line_number) if invalid.

    Older records without hashes are ignored.
    """

    if not AUDIT_FILE.exists():
        return True, None

    previous_hash = GENESIS_HASH

    with AUDIT_FILE.open("r", encoding="utf-8") as file:

        for line_number, line in enumerate(file, start=1):

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return False, line_number

            if not isinstance(event, dict):
                return False, line_number

            # Allow older audit records without hashes.
            if "hash" not in event:
                continue

            stored_hash = event["hash"]

            event_data = event.copy()
            del event_data["hash"]

            if event_data.get("prev_hash") != previous_hash:
                return False, line_number

            calculated_hash = _digest(
                previous_hash,
                event_data,
            )

            if stored_hash != calculated_hash:
                return False, line_number

            previous_hash = stored_hash

    return True, None


def read_audit_events(
    action: str | None = None,
    status: str | None = None,
    approver_id: str | None = None,
    limit: int | None = None,
) -> list[dict]:

    if limit is not None and limit < 0:
        raise ValueError("Limit cannot be negative")

    if not AUDIT_FILE.exists():
        return []

    events = []

    with AUDIT_FILE.open("r", encoding="utf-8") as file:

        for line in file:

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, dict):
                continue

            if action is not None and event.get("action") != action:
                continue

            if status is not None and event.get("status") != status:
                continue

            if approver_id is not None:
                if event.get("approver_id") != approver_id:
                    continue

            events.append(event)

    if limit is not None:
        if limit == 0:
            return []

        events = events[-limit:]

    return events
