import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.main import app, lifespan, run_background_task
import src.main
from redis.exceptions import RedisError

@pytest.fixture
def client():
    return TestClient(app)

def test_unprotected_route(client):
    response = client.get("/unprotected-route")
    assert response.status_code == 200
    assert "Hello, anonym" in response.text

@pytest.mark.asyncio
async def test_background_tasks():
    with patch('src.main.delete_expired_links', new_callable=AsyncMock) as mock_expired, \
         patch('src.main.delete_inactive_links', new_callable=AsyncMock) as mock_inactive, \
         patch('asyncio.sleep', side_effect=Exception('Test exit')):
        
        with pytest.raises(Exception, match='Test exit'):
            await src.main.run_background_task()
            
        mock_expired.assert_awaited()
        mock_inactive.assert_awaited()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_redis():
    with patch('aioredis.from_url', new_callable=MagicMock) as mock:
        yield mock

@pytest.mark.asyncio
async def test_lifespan_shutdown_redis_failure():
    mock_redis = AsyncMock()
    mock_redis.close.side_effect = RedisError("Close failed")
    app.state.redis = mock_redis
    
    async with lifespan(app):
        pass

def test_protected_route_unauthenticated(client):
    with patch('src.main.current_active_user', side_effect=Exception("Not authenticated")):
        response = client.get("/protected-route")
        assert response.status_code in [401, 403]

def test_unprotected_route(client):
    response = client.get("/unprotected-route")
    assert response.status_code == 200
    assert "Hello, anonym" in response.text
