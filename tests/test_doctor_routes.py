"""
Regression tests for POST /api/doctors/register.

Covers a production bug where the route blindly read `result['doctor_id']`
from the service response. Whenever the service returned a malformed
result or raised, that unhandled exception (e.g. KeyError('doctor_id'))
leaked straight into the HTTP response instead of a clean structured error.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.doctors.doctor_routes import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_register_doctor_missing_name_returns_422(client):
    response = client.post("/api/doctors/register", json={})

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "name"] for error in response.json()["detail"]
    )


def test_register_doctor_minimal_payload_succeeds(client):
    fake_result = {
        "success": True,
        "doctor_id": "abc-123",
        "data": {"doctor_id": "abc-123", "name": "Test Doctor"},
    }

    with patch(
        "app.doctors.doctor_routes.doctor_service.register_doctor",
        new=AsyncMock(return_value=fake_result),
    ):
        response = client.post("/api/doctors/register", json={"name": "Test Doctor"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["doctor_id"] == "abc-123"
    assert body["data"] == fake_result["data"]


def test_register_doctor_malformed_service_result_returns_clean_error(client):
    """The service returning a dict without 'doctor_id' must not crash with a raw KeyError."""
    with patch(
        "app.doctors.doctor_routes.doctor_service.register_doctor",
        new=AsyncMock(return_value={"success": True}),
    ):
        response = client.post("/api/doctors/register", json={"name": "Test Doctor"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to register doctor. Please try again later."}


def test_register_doctor_service_exception_does_not_leak_internals(client):
    """A raw exception from the service (e.g. KeyError) must not leak its message to the client."""
    with patch(
        "app.doctors.doctor_routes.doctor_service.register_doctor",
        new=AsyncMock(side_effect=KeyError("doctor_id")),
    ):
        response = client.post("/api/doctors/register", json={"name": "Test Doctor"})

    assert response.status_code == 500
    body = response.json()
    assert "doctor_id" not in body["detail"]
    assert body == {"detail": "Failed to register doctor. Please try again later."}
