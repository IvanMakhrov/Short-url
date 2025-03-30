import json
from src.short_url.cache import (
    cache_link,
    get_cached_link,
    clear_cached_link,
    cache_stats,
    get_cached_stats,
    cache_search_result,
    get_cached_search
)
from src.models import Link
import pytest
from unittest.mock import AsyncMock, patch
from fastapi_cache import FastAPICache

@pytest.fixture
def mock_backend():
    backend = AsyncMock()
    backend.set = AsyncMock()
    backend.get = AsyncMock()
    backend.delete = AsyncMock()
    return backend

@pytest.fixture
def test_link():
    return Link(
        short_code="abc123",
        original_url="https://example.com",
        expires_at=None,
        click_count=5
    )

@pytest.fixture
def test_stats():
    return {
        "original_url": "https://example.com",
        "created_at": None,
        "expires_at": None,
        "click_count": 5,
        "last_accessed": None
    }

@pytest.fixture
def test_search_result():
    return [{
        "short_code": "abc123",
        "created_at": None,
        "expires_at": None,
        "click_count": 5,
        "last_accessed": None
    }]

@pytest.mark.asyncio
async def test_cache_link(mock_backend, test_link):
    with patch.object(FastAPICache, 'get_backend', return_value=mock_backend):
        await cache_link(test_link)
        mock_backend.set.assert_awaited_once()
        args, kwargs = mock_backend.set.call_args
        assert args[0] == "link:abc123"
        assert json.loads(args[1])["original_url"] == "https://example.com"

@pytest.mark.asyncio
async def test_get_cached_link(mock_backend):
    mock_backend.get.return_value = json.dumps({
        'original_url': "https://example.com",
        'expires_at': None,
        'click_count': 5
    })
    
    with patch.object(FastAPICache, 'get_backend', return_value=mock_backend):
        result = await get_cached_link("abc123")
        assert result is not None
        assert result.original_url == "https://example.com"
        assert result.click_count == 5
        mock_backend.get.assert_awaited_once_with("link:abc123")

@pytest.mark.asyncio
async def test_clear_cached_link(mock_backend):
    with patch.object(FastAPICache, 'get_backend', return_value=mock_backend):
        await clear_cached_link("abc123")
        mock_backend.delete.assert_awaited_once_with("link:abc123")

@pytest.mark.asyncio
async def test_cache_stats(mock_backend, test_stats):
    with patch.object(FastAPICache, 'get_backend', return_value=mock_backend):
        await cache_stats("abc123", test_stats)
        mock_backend.set.assert_awaited_with(
            "stats:abc123",
            json.dumps(test_stats),
            expire=300
        )

@pytest.mark.asyncio
async def test_get_cached_stats(mock_backend):
    mock_backend.get.return_value = json.dumps({
        "original_url": "https://example.com",
        "click_count": 5,
        "last_accessed": None
    })
    
    with patch.object(FastAPICache, 'get_backend', return_value=mock_backend):
        stats_result = await get_cached_stats("abc123")
        assert stats_result["original_url"] == "https://example.com"
        assert stats_result["click_count"] == 5
        mock_backend.get.assert_awaited_once_with("stats:abc123")

@pytest.mark.asyncio
async def test_cache_search_result(mock_backend, test_search_result):
    with patch.object(FastAPICache, 'get_backend', return_value=mock_backend):
        await cache_search_result("https://example.com", test_search_result)
        mock_backend.set.assert_awaited_with(
            "search:https://example.com",
            json.dumps(test_search_result),
            expire=600
        )

@pytest.mark.asyncio
async def test_get_cached_search(mock_backend):
    mock_backend.get.return_value = json.dumps([{
        "short_code": "abc123",
        "click_count": 5,
        "created_at": None
    }])
    
    with patch.object(FastAPICache, 'get_backend', return_value=mock_backend):
        search_result = await get_cached_search("https://example.com")
        assert len(search_result) == 1
        assert search_result[0]["short_code"] == "abc123"
        mock_backend.get.assert_awaited_once_with("search:https://example.com")
