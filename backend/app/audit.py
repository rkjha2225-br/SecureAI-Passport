
import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_FILE = Path(__file__).resolve().parents[2] / "audit.log"


def write_audit_event(
    action: str,
    status: str,
    reason: str,
    approver_id: str | None = None,
) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "status": status,
        "reason": reason,
        "approver_id": approver_id,
    }

    with AUDIT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")


def read_audit_events(
    action: str | None = None,
    status: str | None = None,
    approver_id: str | None = None,
) -> list[dict]:

    if not AUDIT_FILE.exists():
        return []

    events = []

    with AUDIT_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if action is not None and event.get("action") != action:
                continue

            if status is not None and event.get("status") != status:
                continue

            if approver_id is not None and event.get("approver_id") != approver_id:
                continue

            events.append(event)

    return events
