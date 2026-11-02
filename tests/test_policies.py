
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend"),
)

from app.policies import check_permission


def test_allowed_action():
    assert check_permission("read_demo_records") is True


def test_forbidden_action():
    assert check_permission("delete_customer_records") is False
