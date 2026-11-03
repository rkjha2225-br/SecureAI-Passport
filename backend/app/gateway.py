
from .audit import write_audit_event
from .approvals import (
    create_approval_request,
    consume_approval,
)
from .policies import check_permission, requires_approval
from .tools import read_demo_records


def execute_action(
    action: str,
    approval_id: str | None = None,
) -> dict:

    # Step 1: Check whether the action is permitted
    if not check_permission(action) and not requires_approval(action):
        reason = "Action is not permitted"

        write_audit_event(
            action,
            "denied",
            reason,
        )

        return {
            "status": "denied",
            "action": action,
            "result": None,
            "reason": reason,
        }

    # Step 2: Handle actions requiring human approval
    if requires_approval(action):

        # No approval ID means approval has not yet been requested
        if approval_id is None:
            approval = create_approval_request(action)

            reason = "Human approval is required before this action can execute"

            write_audit_event(
                action,
                "approval_required",
                reason,
                approval_id=approval["approval_id"],
            )

            return {
                "status": "approval_required",
                "action": action,
                "approval_id": approval["approval_id"],
                "approval_status": approval["status"],
                "result": None,
                "reason": reason,
            }

        # Step 3: Consume the approved request exactly once
        if not consume_approval(approval_id, action):
            reason = "Valid approved request not found or already used"

            write_audit_event(
                action,
                "denied",
                reason,
                approval_id=approval_id,
            )

            return {
                "status": "denied",
                "action": action,
                "result": None,
                "reason": reason,
            }

        # Step 4: Execute the approved action
        # Demonstration only: no actual customer records are deleted.
        reason = "Approved action completed (simulated, no data was deleted)"

        write_audit_event(
            action,
            "executed",
            reason,
            approval_id=approval_id,
        )

        return {
            "status": "executed",
            "action": action,
            "approval_id": approval_id,
            "result": None,
            "reason": reason,
        }

    # Step 5: Execute an immediately permitted action
    if action == "read_demo_records":
        result = read_demo_records()
        reason = "Action completed successfully"

        write_audit_event(
            action,
            "executed",
            reason,
        )

        return {
            "status": "executed",
            "action": action,
            "result": result,
            "reason": reason,
        }

    # Step 6: Deny actions without an executor
    reason = "No executor exists for this action"

    write_audit_event(
        action,
        "denied",
        reason,
    )

    return {
        "status": "denied",
        "action": action,
        "result": None,
        "reason": reason,
    }
