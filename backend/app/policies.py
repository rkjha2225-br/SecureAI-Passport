
ALLOWED_ACTIONS = {
    "read_demo_records",
}

APPROVAL_REQUIRED_ACTIONS = {
    "delete_customer_records",
}


def check_permission(action: str) -> bool:
    return action in ALLOWED_ACTIONS


def requires_approval(action: str) -> bool:
    return action in APPROVAL_REQUIRED_ACTIONS
if ALLOWED_ACTIONS & APPROVAL_REQUIRED_ACTIONS:
        raise ValueError(
            "An action cannot be both allowed and approval-required"
        )
