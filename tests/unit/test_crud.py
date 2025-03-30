import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from src.short_url.crud import (
    generate_short_code,
    normalize_url,
    check_short_link_exists,
    create_link,
    get_link_by_short_code,
    update_link_stats,
    delete_link,
    update_link,
    get_link_stats,
    search_link_by_url,
    delete_expired_links,
    delete_inactive_links,
    count_clicks_in_cache
)
from src.short_url.schemas import LinkCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@pytest.mark.asyncio
async def test_generate_short_code():
    url = "https://example.com"
    code = generate_short_code(url)
    assert len(code) == 6
    assert isinstance(code, str)
    assert generate_short_code(url) == code
    assert generate_short_code("https://example.com/1") != code

def test_normalize_url():
    assert normalize_url("https://example.com") == "https://example.com"
    assert normalize_url("https://example.com/") == "https://example.com"
    assert normalize_url("https://example.com/path/") == "https://example.com/path"
    assert normalize_url("https://example.com?query=param") == "https://example.com?query=param"
    assert normalize_url("http://example.com") == "http://example.com"
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("https://EXAMPLE.COM") == "https://example.com"
    assert normalize_url("https://example.com/%7Euser") == "https://example.com/~user"
    assert normalize_url("") == ""
    assert normalize_url(None) is None

@pytest.mark.asyncio
async def test_check_short_link_exists_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = "found_link"
    
    with patch('src.short_url.crud.select', return_value=MagicMock()) as mock_select:
        mock_select.return_value.where.return_value = mock_select.return_value
        mock_session.execute.return_value = mock_result
        
        result = await check_short_link_exists(mock_session, "abc123")
        assert result == "found_link"

@pytest.mark.asyncio
async def test_check_short_link_exists_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    
    with patch('src.short_url.crud.select', return_value=MagicMock()) as mock_select:
        mock_select.return_value.where.return_value = mock_select.return_value
        mock_session.execute.return_value = mock_result
        
        result = await check_short_link_exists(mock_session, "abc123")
        assert result is None

@pytest.mark.asyncio
async def test_create_link(mocker):
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mocker.patch(
        "src.short_url.crud.check_short_link_exists",
        return_value=None
    )

    link_data = LinkCreate(
        original_url="https://example.com",
        custom_alias=None,
        expires_at=None
    )

    result = await create_link(mock_session, link_data)
    assert result is not None
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_link_with_custom_alias(mocker):
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mocker.patch(
        "src.short_url.crud.check_short_link_exists",
        return_value=None
    )

    link_data = LinkCreate(
        original_url="https://example.com",
        custom_alias="custom",
        expires_at=datetime.now() + timedelta(days=7)
    )

    result = await create_link(mock_session, link_data)
    assert result is not None
    assert result.short_code == "custom"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_link_by_short_code_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    
    with patch('src.short_url.crud.select', return_value=MagicMock()) as mock_select:
        mock_select.return_value.where.return_value = mock_select.return_value
        mock_session.execute.return_value = mock_result
        
        result = await get_link_by_short_code(mock_session, "abc123")
        assert result is None

@pytest.mark.asyncio
async def test_update_link_stats():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_link = MagicMock()
    mock_link.click_count = 0
    mock_session.commit = AsyncMock()

    before_last_accessed = mock_link.last_accessed
    await update_link_stats(mock_session, mock_link)
    assert mock_link.click_count == 1
    assert mock_link.last_accessed != before_last_accessed
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_link_success():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    
    with patch('src.short_url.crud.check_short_link_exists', return_value=MagicMock()):
        result = await delete_link(mock_session, "abc123")
        assert result is True
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_link_success():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    
    with patch('src.short_url.crud.check_short_link_exists', return_value=MagicMock()):
        result = await update_link(mock_session, "abc123", "https://new-url.com")
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_link_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch('src.short_url.crud.check_short_link_exists', return_value=None):
        result = await update_link(mock_session, "abc123", "https://new-url.com")
        assert result is False
        mock_session.execute.assert_not_called()

@pytest.mark.asyncio
async def test_get_link_stats_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch('src.short_url.crud.get_link_by_short_code', return_value=None):
        result = await get_link_stats(mock_session, "abc123")
        assert result is None

@pytest.mark.asyncio
async def test_search_link_by_url_empty():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.all.return_value = []
    
    with patch('src.short_url.crud.select', return_value=MagicMock()) as mock_select:
        mock_select.return_value.where.return_value = mock_select.return_value
        mock_session.execute.return_value = mock_result
        
        results = await search_link_by_url(mock_session, "https://example.com")
        assert len(results) == 0

@pytest.mark.asyncio
async def test_delete_expired_links():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    
    mock_link1 = MagicMock()
    mock_link2 = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_link1, mock_link2]
    
    with patch('src.short_url.crud.select', return_value=MagicMock()) as mock_select:
        mock_select.return_value.where.return_value = mock_select.return_value
        mock_session.execute.return_value = mock_result
        
        await delete_expired_links(mock_session)
        assert mock_session.delete.call_count == 2
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_inactive_links():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    
    mock_link1 = MagicMock(link_id=1)
    mock_link2 = MagicMock(link_id=2)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_link1, mock_link2]
    
    with patch('src.short_url.crud.select', return_value=MagicMock()) as mock_select:
        mock_select.return_value.where.return_value = mock_select.return_value
        mock_session.execute.return_value = mock_result
        
        result = await delete_inactive_links(mock_session, days=7)
        assert result["deleted_count"] == 2
        mock_session.execute.assert_called()
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_inactive_links_none_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    
    with patch('src.short_url.crud.select', return_value=MagicMock()) as mock_select:
        mock_select.return_value.where.return_value = mock_select.return_value
        mock_session.execute.return_value = mock_result
        
        result = await delete_inactive_links(mock_session, days=7)
        assert result["deleted_count"] == 0
        mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_count_clicks_in_cache():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    
    result = await count_clicks_in_cache(mock_session, "abc123")
    assert result == {"added click from cache": "abc123"}
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_normalize_url_with_unicode():
    url = "https://example.com/üniçode"
    normalized = normalize_url(url)
    assert "üniçode" in normalized
