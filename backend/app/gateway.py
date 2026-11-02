
from .audit import write_audit_event
from .approvals import create_approval_request
from .policies import check_permission, requires_approval
from .tools import read_demo_records


def execute_action(action: str) -> dict:

    if requires_approval(action):
        approval = create_approval_request(action)
        reason = "Human approval is required before this action can execute"

        write_audit_event(action, "approval_required", reason)

        return {
        "status": "approval_required",
        "action": action,
        "approval_id": approval["approval_id"],
        "approval_status": approval["status"],
        "result": None,
        "reason": reason,
         }


    if not check_permission(action):
        reason = "Action is not permitted"

        write_audit_event(action, "denied", reason)

        return {
            "status": "denied",
            "action": action,
            "result": None,
            "reason": reason,
        }

    if action == "read_demo_records":
        result = read_demo_records()
        reason = "Action completed successfully"

        write_audit_event(action, "executed", reason)

        return {
            "status": "executed",
            "action": action,
            "result": result,
            "reason": reason,
        }

    reason = "No executor exists for this action"

    write_audit_event(action, "denied", reason)

    return {
        "status": "denied",
        "action": action,
        "result": None,
        "reason": reason,
    }
