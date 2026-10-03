import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import uuid

from app.main import app
from app.db.session import get_db
from app.shared.security.dependencies import get_current_user

@pytest.fixture
def test_db():
    # Mock database session to handle PostgreSQL specific types gracefully
    mock_db = MagicMock()
    yield mock_db

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    return user

@pytest.fixture
def test_client(test_db, mock_user):
    def override_get_db():
        yield test_db

    def override_get_current_user():
        return mock_user
        
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password": "StrongPassword123!"
    }

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_token"}
