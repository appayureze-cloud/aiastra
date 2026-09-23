"""
Regression tests for POST /api/ai-agent/ask.

Covers a bug where the route's own `HTTPException(503, "AI model not
initialized...")` was caught by its own broad `except Exception` and
re-wrapped as a 500 with the original detail string concatenated into a
new message (losing the correct status code and leaking internal text).
Unexpected exceptions from the model client were also leaked verbatim
to the client instead of returning a clean, generic error.
"""

import sys
import types
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _install_fake_main_enhanced(model_inference):
    """app.ai_agent_api imports `model_inference` from main_enhanced lazily,
    inside the request handler. Stub that module so tests don't have to
    import the real (heavy, ML-dependent) entrypoint."""
    fake_module = types.ModuleType("main_enhanced")
    fake_module.model_inference = model_inference
    sys.modules["main_enhanced"] = fake_module


@pytest.fixture
def client():
    from app.ai_agent_api import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup_fake_module():
    yield
    sys.modules.pop("main_enhanced", None)


def test_ask_missing_question_returns_422(client):
    response = client.post("/api/ai-agent/ask", json={})

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "question"] for error in response.json()["detail"]
    )


def test_ask_happy_path_returns_answer(client):
    fake_model = AsyncMock()
    fake_model.generate_response = AsyncMock(return_value="Ginger tea helps digestion.")
    _install_fake_main_enhanced(fake_model)

    response = client.post("/api/ai-agent/ask", json={"question": "How to improve digestion?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Ginger tea helps digestion."
    assert body["language"] == "en"


def test_ask_model_not_initialized_returns_503_not_500(client):
    """The deliberate 503 must survive, not get re-wrapped into a 500."""
    _install_fake_main_enhanced(None)

    response = client.post("/api/ai-agent/ask", json={"question": "hello"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": "AI model not initialized. Please wait for server to fully start."
    }


def test_ask_unexpected_exception_does_not_leak_internals(client):
    fake_model = AsyncMock()
    fake_model.generate_response = AsyncMock(
        side_effect=RuntimeError("connection refused to internal-host:9999")
    )
    _install_fake_main_enhanced(fake_model)

    response = client.post("/api/ai-agent/ask", json={"question": "hello"})

    assert response.status_code == 500
    body = response.json()
    assert "internal-host" not in body["detail"]
    assert body == {"detail": "Failed to generate AI response. Please try again later."}
