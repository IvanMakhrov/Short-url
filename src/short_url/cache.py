from fastapi_cache import FastAPICache
from src.models import Link
import json
import datetime
from typing import Optional

async def cache_link(link: Link):
    backend = FastAPICache.get_backend()
    await backend.set(
        f"link:{link.short_code}",
        json.dumps({
            'original_url': link.original_url,
            'expires_at': link.expires_at.isoformat() if link.expires_at else None,
            'click_count': link.click_count
        }),
        expire=3600
    )

async def get_cached_link(short_code: str) -> Optional[Link]:
    backend = FastAPICache.get_backend()
    cached = await backend.get(f"link:{short_code}")
    if cached:
        data = json.loads(cached)
        return Link(
            short_code=short_code,
            original_url=data['original_url'],
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            click_count=data['click_count']
        )
    return None

async def clear_cached_link(short_code: str):
    backend = FastAPICache.get_backend()
    if hasattr(backend, "delete"):
        await backend.delete(f"link:{short_code}")
    else:
        await backend.set(f"link:{short_code}", "", expire=1)

async def cache_stats(short_code: str, stats: dict):
    backend = FastAPICache.get_backend()
    await backend.set(
        f"stats:{short_code}",
        json.dumps({
            "original_url": stats.get('original_url'),
            "created_at": stats.get('created_at', None).isoformat() if stats.get('created_at', None) else None,
            'expires_at': stats.get('expires_at', None).isoformat() if stats.get('expires_at', None) else None,
            "click_count": stats.get('click_count'),
            "last_accessed": stats.get('last_accessed', None).isoformat() if stats.get('last_accessed', None) else None
        }),
        expire=300
    )

async def get_cached_stats(short_code: str) -> Optional[dict]:
    backend = FastAPICache.get_backend()
    cached = await backend.get(f"stats:{short_code}")
    return json.loads(cached) if cached else None

async def cache_search_result(original_url: str, links: list[Link]):
    backend = FastAPICache.get_backend()
    await backend.set(
        f"search:{original_url}",
        json.dumps([{
            'short_code': link.get('short_code'),
            'created_at': link.get('created_at', None).isoformat() if link.get('created_at', None) else None,
            'expires_at': link.get('expires_at', None).isoformat() if link.get('expires_at', None) else None,
            'click_count': link.get('click_count'),
            'last_accessed': link.get('last_accessed', None).isoformat() if link.get('last_accessed', None) else None
        } for link in links]),
        expire=600
    )

async def get_cached_search(original_url: str) -> Optional[list[Link]]:
    backend = FastAPICache.get_backend()
    cached = await backend.get(f"search:{original_url}")
    return json.loads(cached) if cached else None
