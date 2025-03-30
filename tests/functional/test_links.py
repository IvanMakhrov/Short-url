import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from src.auth.users import current_active_user, current_active_user_optional
from src.auth.db import User

client = TestClient(app)

test_user = User(
    id=1,
    email="test@example.com",
    hashed_password="hashed_password",
    is_active=True,
    is_superuser=False,
    is_verified=True
)

@pytest.fixture
def mock_db_session(mocker):
    mock_session = AsyncMock()
    mocker.patch("src.database.get_async_session", return_value=mock_session)
    return mock_session

@pytest.fixture
def mock_current_user(mocker):
    mocker.patch("src.auth.users.current_active_user", return_value=test_user)

@pytest.fixture
def mock_current_user_optional(mocker):
    mocker.patch("src.auth.users.current_active_user_optional", return_value=test_user)

def test_create_short_link_unauthenticated(mock_db_session, mock_current_user_optional):
    with patch("src.short_url.crud.create_link", return_value=AsyncMock(short_code="abc123")):
        response = client.post(
            "/links/shorten",
            json={
                "original_url": "https://example.com",
                "custom_alias": None,
                "expires_at": None
            }
        )
        assert response.status_code == status.HTTP_200_OK
        assert "abc123" in response.json()["short_code"]

def test_create_short_link_with_existing_alias(mock_db_session, mock_current_user_optional):
    with patch("src.short_url.crud.create_link", return_value=False):
        response = client.post(
            "/links/shorten",
            json={
                "original_url": "https://example.com",
                "custom_alias": "existing",
                "expires_at": None
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_redirect_to_original_expired(mock_db_session):
    mock_link = AsyncMock()
    mock_link.original_url = "https://example.com"
    mock_link.expires_at = datetime.now() - timedelta(days=1)
    
    with patch("src.short_url.crud.get_link_by_short_code", return_value=mock_link):
        response = client.get("/links/abc123")
        assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_link_stats(mock_db_session):
    stats_data = {
        "original_url": "https://example.com",
        "created_at": datetime.now(),
        "expires_at": None,
        "click_count": 5,
        "last_accessed": datetime.now()
    }
    
    with patch("src.short_url.crud.get_link_stats", return_value=stats_data), \
         patch("src.short_url.cache.cache_stats", new_callable=AsyncMock):
        
        response = client.get("/links/abc123/stats")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["original_url"] == "https://example.com"
        assert response.json()["click_count"] == 5

def test_search_link_by_url(mock_db_session):
    search_results = [{
        "short_code": "abc123",
        "created_at": datetime.now(),
        "expires_at": None,
        "click_count": 5,
        "last_accessed": datetime.now()
    }]
    
    with patch("src.short_url.crud.search_link_by_url", return_value=search_results), \
         patch("src.short_url.cache.cache_search_result", new_callable=AsyncMock):
        
        response = client.get("/links/search/https://example.com")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        assert response.json()[0]["short_code"] == "abc123"
