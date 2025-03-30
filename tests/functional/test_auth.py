import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app
from src.auth.db import User

client = TestClient(app)

@pytest.fixture
def mock_user_manager():
    with patch('src.auth.users.UserManager', autospec=True) as mock:
        instance = mock.return_value
        instance.authenticate = AsyncMock()
        instance.current_user = AsyncMock()
        yield instance

@pytest.fixture
def test_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )

def test_login_user(mock_user_manager, test_user):
    mock_user_manager.authenticate.return_value = test_user
    mock_user_manager.current_user.return_value = test_user
    
    with patch('src.auth.users.JWTStrategy.write_token') as mock_write_token:
        mock_write_token.return_value = "test_token"
        
        response = client.post(
            "/auth/jwt/login",
            data={"username": "test@example.com", "password": "password"}
        )
        
        print(f"Login response: {response.status_code}, {response.json()}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == "test_token"
