
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend"),
)

from app.audit import read_audit_events

from app.gateway import execute_action


def test_allowed_action_executes():
    response = execute_action("read_demo_records")

    assert response["status"] == "executed"
    assert len(response["result"]) == 3



def test_forbidden_action_requires_approval():
    response = execute_action("delete_customer_records")

    assert response["status"] == "approval_required"
    assert response["result"] is None

def test_sensitive_action_never_executes_through_gateway():
        response = execute_action("delete_customer_records")

        assert response["status"] == "approval_required"
        assert response["result"] is None

def test_denied_action_is_recorded_in_audit_log():
            response = execute_action("delete_customer_records")

            events = read_audit_events()

            assert response["status"] == "approval_required"
            assert any(
                event["action"] == "delete_customer_records"
                and event["status"] == "approval_required"
                for event in events
            )
