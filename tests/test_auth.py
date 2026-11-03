import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend"),
)

# Test authentication configuration
os.environ["SECUREAI_API_KEY"] = "test-key-for-automated-tests"
os.environ["SECUREAI_APPROVER_TOKEN"] = "test-approver-token-for-automated-tests"
os.environ["SECUREAI_APPROVER_ID"] = "approver-001"

from app.approvals import create_approval_request
from app.main import app

client = TestClient(app)

API_HEADERS = {
    "X-API-Key": "test-key-for-automated-tests",
}

APPROVER_HEADERS = {
    **API_HEADERS,
    "X-Approver-Token": "test-approver-token-for-automated-tests",
}
