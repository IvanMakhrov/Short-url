import pytest
from unittest.mock import AsyncMock, patch
from fastapi_cache import FastAPICache
from src.short_url.cache import (
    cache_link,
    get_cached_link,
    cache_stats,
)
from src.models import Link
import json

@pytest.fixture(autouse=True)
async def setup_cache():
    mock_backend = AsyncMock()
    FastAPICache.init(mock_backend)
    yield
    await FastAPICache.clear()

@pytest.mark.asyncio
async def test_cache_miss_handling():
    mock_backend = AsyncMock()
    mock_backend.get.return_value = None
    with patch('src.short_url.cache.FastAPICache.get_backend', return_value=mock_backend):
        result = await get_cached_link("missing123")
        assert result is None
        mock_backend.get.assert_awaited_once_with("link:missing123")

@pytest.mark.asyncio
async def test_cache_stats_with_none_values():
    stats = {
        "original_url": "https://example.com",
        "created_at": None,
        "expires_at": None,
        "click_count": 0,
        "last_accessed": None
    }
    
    mock_backend = AsyncMock()
    with patch('src.short_url.cache.FastAPICache.get_backend', return_value=mock_backend):
        await cache_stats("test123", stats)
        mock_backend.set.assert_awaited_once_with(
            "stats:test123",
            json.dumps({
                "original_url": "https://example.com",
                "created_at": None,
                "expires_at": None,
                "click_count": 0,
                "last_accessed": None
            }),
            expire=300
        )

@pytest.mark.asyncio
async def test_cache_link_roundtrip():
    test_link = Link(
        short_code="abc123",
        original_url="https://example.com",
        expires_at=None,
        click_count=5
    )
    
    mock_backend = AsyncMock()
    with patch('src.short_url.cache.FastAPICache.get_backend', return_value=mock_backend):
        await cache_link(test_link)
        mock_backend.set.assert_awaited_once()
        
        mock_backend.get.return_value = json.dumps({
            'original_url': 'https://example.com',
            'expires_at': test_link.expires_at,
            'click_count': 5
        })
        cached = await get_cached_link("abc123")
        assert cached.original_url == "https://example.com"
        assert cached.click_count == 5
