import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from src.main import app
from src.auth.db import User
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


FastAPICache.init(InMemoryBackend())

client = TestClient(app)


TEST_USER = User(
    id=1,
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    is_superuser=False,
    is_verified=True
)

@pytest.fixture(autouse=True)
async def setup_cache():
    mock_backend = AsyncMock()
    FastAPICache.init(mock_backend)
    yield
    await FastAPICache.clear()

def get_serialized_link_data():
    return {
        "original_url": "https://example.com/path?query=param",
        "custom_alias": None,
        "expires_at": None
    }

@pytest.fixture
def mock_link():
    link = MagicMock()
    link.short_code = "test123"
    link.original_url = "https://example.com"
    link.expires_at = datetime.now() + timedelta(days=1)
    link.user_id = 1
    link.click_count = 0
    link.__json__ = lambda self: {
        "short_code": self.short_code,
        "original_url": self.original_url,
        "expires_at": self.expires_at.isoformat(),
        "user_id": self.user_id,
        "click_count": self.click_count
    }
    return link

def test_create_short_link_unauthenticated(mock_link):
    test_data = get_serialized_link_data()
    
    with patch('src.short_url.crud.create_link', new_callable=AsyncMock) as mock_create, \
         patch('src.short_url.cache.get_cached_link', new_callable=AsyncMock, return_value=None), \
         patch('src.short_url.crud.check_short_link_exists', new_callable=AsyncMock, return_value=None):
        
        mock_create.return_value = mock_link
        
        response = client.post(
            "/links/shorten",
            json=test_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "test123" in response.json()["short_code"]


def test_create_link_with_existing_alias():
    test_data = {
        "original_url": "https://example.com",
        "custom_alias": "existing",
        "expires_at": None
    }
    
    with patch('src.short_url.cache.get_cached_link', new_callable=AsyncMock) as mock_cache, \
         patch('src.short_url.crud.check_short_link_exists', new_callable=AsyncMock) as mock_check:
        
        mock_cache.return_value = MagicMock()
        mock_check.return_value = MagicMock()
        
        response = client.post(
            "/links/shorten",
            json=test_data
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

def test_redirect_with_db_link(mock_link):
    with patch('src.short_url.crud.get_link_by_short_code', new_callable=AsyncMock) as mock_get, \
         patch('src.short_url.crud.update_link_stats', new_callable=AsyncMock), \
         patch('src.short_url.cache.cache_link', new_callable=AsyncMock):
        
        mock_get.return_value = mock_link
        response = client.get("/links/test123", follow_redirects=False)
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

def test_redirect_expired_link(mock_link):
    mock_link.expires_at = datetime.now() - timedelta(days=1)
    
    with patch('src.short_url.crud.get_link_by_short_code', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_link
        response = client.get("/links/expired123")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "expired" in response.json()["detail"]

def test_delete_link_unauthorized(mock_link):
    other_user = User(
        id=2,
        email="other@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    
    with patch('src.short_url.crud.get_link_by_short_code', new_callable=AsyncMock) as mock_get, \
         patch('src.auth.users.current_active_user', return_value=other_user):
        
        mock_get.return_value = mock_link
        response = client.delete(
            "/links/test123",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_link_stats_with_db_data(mock_link):
    db_stats = {
        "original_url": "https://example.com",
        "click_count": 10,
        "last_accessed": datetime.now()
    }
    
    with patch('src.short_url.crud.get_link_stats', new_callable=AsyncMock) as mock_stats, \
         patch('src.short_url.cache.cache_stats', new_callable=AsyncMock):
        
        mock_stats.return_value = db_stats
        response = client.get("/links/test123/stats")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["click_count"] == 10

def test_search_link_not_found():
    with patch('src.short_url.crud.search_link_by_url', new_callable=AsyncMock) as mock_search, \
         patch('src.short_url.cache.get_cached_search', new_callable=AsyncMock, return_value=None):
        
        mock_search.return_value = None
        response = client.get("/links/search/https://nonexistent.com")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

def test_redirect_nonexistent_link():
    with patch('src.short_url.crud.get_link_by_short_code', new_callable=AsyncMock) as mock_get, \
         patch('src.short_url.cache.get_cached_link', new_callable=AsyncMock, return_value=None):
        
        mock_get.return_value = None
        response = client.get("/links/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

def test_search_link_with_special_chars():
    test_url = "https://example.com/path?query=param&another=value"
    
    with patch('src.short_url.crud.search_link_by_url', new_callable=AsyncMock) as mock_search, \
         patch('src.short_url.cache.cache_search_result', new_callable=AsyncMock):
        
        mock_link = MagicMock()
        mock_link.short_code = "test123"
        mock_search.return_value = mock_link
        
        response = client.get(f"/links/search/{test_url}")
        assert response.status_code == status.HTTP_200_OK

def test_create_short_link_with_db_failure():
    test_data = {
        "original_url": "https://example.com",
        "custom_alias": "testalias",
        "expires_at": None
    }
    
    with patch('src.short_url.cache.get_cached_link', new_callable=AsyncMock, return_value=None), \
         patch('src.short_url.crud.create_link', new_callable=AsyncMock, return_value=None), \
         patch('src.auth.users.current_active_user_optional', return_value=None):
        
        response = client.post("/links/shorten", json=test_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

def test_get_stats_with_cache_set_failure():
    db_stats = {
        "original_url": "https://example.com",
        "click_count": 10,
        "last_accessed": datetime.now().isoformat()
    }
    
    with patch('src.short_url.crud.get_link_stats', new_callable=AsyncMock, return_value=db_stats), \
         patch('src.short_url.cache.cache_stats', new_callable=AsyncMock, side_effect=Exception("Cache Error")), \
         patch('src.short_url.cache.get_cached_stats', new_callable=AsyncMock, return_value=None):
        
        response = client.get("/links/test123/stats")
        assert response.status_code == status.HTTP_200_OK

def test_search_link_with_cache_set_failure():
    mock_link = MagicMock()
    mock_link.short_code = "test123"
    mock_link.original_url = "https://example.com"
    
    with patch('src.short_url.crud.search_link_by_url', new_callable=AsyncMock, return_value=mock_link), \
         patch('src.short_url.cache.cache_search_result', new_callable=AsyncMock, side_effect=Exception("Cache Error")), \
         patch('src.short_url.cache.get_cached_search', new_callable=AsyncMock, return_value=None):
        
        response = client.get("/links/search/https://example.com")
        assert response.status_code == status.HTTP_200_OK

def test_create_short_link_with_invalid_expiration():
    test_data = {
        "original_url": "https://example.com",
        "custom_alias": None,
        "expires_at": "invalid-date"
    }
    
    response = client.post("/links/shorten", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
