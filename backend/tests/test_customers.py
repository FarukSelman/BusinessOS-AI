import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_customer_service():
    with patch("app.modules.customers.router.get_service") as mock_get_service:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        yield mock_service

@pytest.fixture
def customer_data():
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "0987654321"
    }

def test_create_customer(test_client, customer_data, mock_customer_service, auth_headers):
    """Test creating a customer."""
    mock_customer_service.create.return_value = {"id": "uuid", **customer_data}
    response = test_client.post("/api/v1/customers", json=customer_data, headers=auth_headers)
    assert response.status_code in [200, 201]

def test_list_customers(test_client, mock_customer_service, auth_headers):
    """Test listing customers."""
    mock_customer_service.list.return_value = [{"id": "uuid", "first_name": "Jane"}]
    response = test_client.get("/api/v1/customers", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_customer(test_client, mock_customer_service, auth_headers):
    """Test updating a customer."""
    customer_id = "123e4567-e89b-12d3-a456-426614174000"
    update_data = {"first_name": "Janet"}
    mock_customer_service.update.return_value = {"id": customer_id, "first_name": "Janet"}
    response = test_client.patch(f"/api/v1/customers/{customer_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200

def test_delete_customer(test_client, mock_customer_service, auth_headers):
    """Test deleting a customer."""
    customer_id = "123e4567-e89b-12d3-a456-426614174000"
    response = test_client.delete(f"/api/v1/customers/{customer_id}", headers=auth_headers)
    assert response.status_code in [200, 204]

def test_create_customer_unauthenticated(test_client, customer_data):
    """Test that creating a customer fails if unauthenticated."""
    from app.shared.security.dependencies import get_current_user
    from app.main import app
    app.dependency_overrides.pop(get_current_user, None)
    
    response = test_client.post("/api/v1/customers", json=customer_data)
    assert response.status_code == 401
