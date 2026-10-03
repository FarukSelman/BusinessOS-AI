import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_business_service():
    with patch("app.modules.business.router.get_service") as mock_get_service:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        yield mock_service

@pytest.fixture
def business_data():
    return {
        "name": "Test Business",
        "industry": "Software",
        "email": "contact@testbusiness.com",
        "phone": "1234567890"
    }

def test_create_business(test_client, business_data, mock_business_service, auth_headers):
    """Create a new business."""
    mock_business_service.create.return_value = {"id": "uuid", **business_data}
    response = test_client.post("/api/v1/businesses", json=business_data, headers=auth_headers)
    assert response.status_code in [200, 201]

def test_list_businesses(test_client, mock_business_service, auth_headers):
    """List user's businesses."""
    mock_business_service.list_for_user.return_value = [{"id": "uuid", "name": "Test Business"}]
    response = test_client.get("/api/v1/businesses", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_business(test_client, mock_business_service, auth_headers):
    """Get business by ID."""
    business_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_business_service.get.return_value = {"id": business_id, "name": "Test Business"}
    # Using permission overrides or assuming test_client uses mock_user that bypasses permissions for simplicity
    response = test_client.get(f"/api/v1/businesses/{business_id}", headers=auth_headers)
    assert response.status_code == 200

def test_update_business(test_client, mock_business_service, auth_headers):
    """Update business info."""
    business_id = "123e4567-e89b-12d3-a456-426614174000"
    update_data = {"name": "Updated Name"}
    mock_business_service.update.return_value = {"id": business_id, "name": "Updated Name"}
    response = test_client.patch(f"/api/v1/businesses/{business_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200

def test_create_business_duplicate_email(test_client, business_data, mock_business_service, auth_headers):
    """Should fail if business email is duplicate."""
    from fastapi import HTTPException
    mock_business_service.create.side_effect = HTTPException(status_code=409, detail="Email already exists")
    response = test_client.post("/api/v1/businesses", json=business_data, headers=auth_headers)
    assert response.status_code == 409
