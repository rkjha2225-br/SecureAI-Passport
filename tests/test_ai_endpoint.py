
import sys
import os
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend")
)

from fastapi.testclient import TestClient
from app.main import app
import app.main as main
from app.auth import require_api_key


os.environ.setdefault(
    "SECUREAI_API_KEY",
    "dev-only-change-this-key-9f2a"
)

client = TestClient(app)

headers = {
    "X-API-Key": "dev-only-change-this-key-9f2a"
}


def test_ai_success(monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides,
        require_api_key,
        lambda: "test-key"
    )

    monkeypatch.setattr(
        main,
        "understand_request",
        lambda message: "read_demo_records"
    )

    monkeypatch.setattr(
        main,
        "execute_action",
        lambda action: {"status": "executed"}
    )

    response = client.post(
        "/ai/execute",
        json={"user_message": "Show demo records"},
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "executed"


def test_ai_unclear_request(monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides,
        require_api_key,
        lambda: "test-key"
    )

    def fake_ai(message):
        raise ValueError("Unsupported action")

    monkeypatch.setattr(main, "understand_request", fake_ai)

    response = client.post(
        "/ai/execute",
        json={"user_message": "Do something"},
        headers=headers
    )

    assert response.status_code == 400


def test_ai_service_failure(monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides,
        require_api_key,
        lambda: "test-key"
    )

    def fake_ai(message):
        raise RuntimeError("AI service unavailable")

    monkeypatch.setattr(main, "understand_request", fake_ai)

    response = client.post(
        "/ai/execute",
        json={"user_message": "Show demo records"},
        headers=headers
    )

    assert response.status_code == 503


def test_ai_empty_message(monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides,
        require_api_key,
        lambda: "test-key"
    )

    response = client.post(
        "/ai/execute",
        json={"user_message": ""},
        headers=headers
    )

    assert response.status_code == 422
