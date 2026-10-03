import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_appointment_service():
    with patch("app.modules.appointments.router.get_service") as mock_get_service:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        yield mock_service

@pytest.fixture
def appointment_data():
    return {
        "title": "Consultation",
        "start_time": "2026-08-01T10:00:00Z",
        "end_time": "2026-08-01T11:00:00Z",
        "customer_id": "123e4567-e89b-12d3-a456-426614174000"
    }

def test_create_appointment(test_client, appointment_data, mock_appointment_service, auth_headers):
    """Test creating an appointment."""
    mock_appointment_service.create.return_value = {"id": "uuid", **appointment_data}
    response = test_client.post("/api/v1/appointments", json=appointment_data, headers=auth_headers)
    assert response.status_code in [200, 201]

def test_list_appointments(test_client, mock_appointment_service, auth_headers):
    """Test listing appointments."""
    mock_appointment_service.list.return_value = [{"id": "uuid", "title": "Consultation"}]
    response = test_client.get("/api/v1/appointments", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_cancel_appointment(test_client, mock_appointment_service, auth_headers):
    """Test canceling an appointment."""
    appointment_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_appointment_service.cancel.return_value = {"id": appointment_id, "status": "canceled"}
    response = test_client.post(f"/api/v1/appointments/{appointment_id}/cancel", headers=auth_headers)
    assert response.status_code == 200

def test_complete_appointment(test_client, mock_appointment_service, auth_headers):
    """Test completing an appointment."""
    appointment_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_appointment_service.complete.return_value = {"id": appointment_id, "status": "completed"}
    response = test_client.post(f"/api/v1/appointments/{appointment_id}/complete", headers=auth_headers)
    assert response.status_code == 200

def test_get_available_slots(test_client, mock_appointment_service, auth_headers):
    """Test getting available slots."""
    mock_appointment_service.get_available_slots.return_value = ["2026-08-01T10:00:00Z", "2026-08-01T11:00:00Z"]
    response = test_client.get("/api/v1/appointments/slots", params={"date": "2026-08-01"}, headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
