from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_, or_
from src.short_url.schemas import LinkCreate
import src.models as models
import hashlib
import datetime
from urllib.parse import urlparse, unquote

def generate_short_code(url: str):
    return hashlib.md5(url.encode()).hexdigest()[:6]

def normalize_url(url: str) -> str:
    if not url:
        return url
    
    decoded = unquote(url)
    parsed = urlparse(decoded)
    scheme = parsed.scheme.lower() if parsed.scheme else 'https'
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/')
    normalized = f"{scheme}://{netloc}{path}"

    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized

async def check_short_link_exists(db: AsyncSession, short_code: str):
    stmt = select(models.Link).where(models.Link.short_code == short_code)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_link(db: AsyncSession, link: LinkCreate, user_id: int = None):
    normalized_url = normalize_url(link.original_url)
    short_code = link.custom_alias if link.custom_alias else generate_short_code(normalized_url)
    short_link_flag = await check_short_link_exists(db, short_code)

    if short_link_flag:
        return False

    db_link = models.Link(
        original_url=normalized_url,
        short_code=short_code,
        expires_at=link.expires_at,
        user_id=user_id
    )
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link

async def get_link_by_short_code(db: AsyncSession, short_code: str):
    stmt = select(models.Link).where(models.Link.short_code == short_code)
    result = await db.execute(stmt)
    return result.scalars().first()

async def update_link_stats(db: AsyncSession, link: models.Link):
    link.click_count += 1
    link.last_accessed = datetime.datetime.now()
    await db.commit()

async def delete_link(db: AsyncSession, short_code: str):
    short_link_flag = await check_short_link_exists(db, short_code)

    if short_link_flag:
        await db.delete(short_link_flag)
        await db.commit()
        return True
    return False

async def update_link(db: AsyncSession, short_code: str, new_url: str):
    normalized_url = normalize_url(new_url)
    short_link_flag = await check_short_link_exists(db, short_code)

    if short_link_flag:
        stmt = (
            update(models.Link)
            .where(models.Link.short_code == short_code)
            .values(original_url=normalized_url)
        )
        await db.execute(stmt)
        await db.commit()
        return True
    return False

async def get_link_stats(db: AsyncSession, short_code: str):
    link = await get_link_by_short_code(db, short_code)
    if link:
        return {
            "original_url": link.original_url,
            "created_at": link.created_at,
            "expires_at": link.expires_at,
            "click_count": link.click_count,
            "last_accessed": link.last_accessed
        }
    return None

async def search_link_by_url(db: AsyncSession, original_url: str):
    normalized_url = normalize_url(original_url)
    stmt = select(
        models.Link.short_code,
        models.Link.created_at,
        models.Link.click_count,
        models.Link.expires_at,
        models.Link.last_accessed
    ).where(
        models.Link.original_url == normalized_url
    )
    result = await db.execute(stmt)
    return [
        {
            'short_code': row.short_code,
            'created_at': row.created_at,
            'expires_at': row.expires_at,
            'click_count': row.click_count,
            'last_accessed': row.last_accessed
        }
        for row in result
    ]

async def delete_expired_links(db: AsyncSession):
    link = select(models.Link).where(models.Link.expires_at < datetime.datetime.now())
    result = await db.execute(link)
    expired_links = result.scalars().all()

    for link in expired_links:
        await db.delete(link)
    await db.commit()

async def delete_inactive_links(db: AsyncSession, days: int=1):
    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=days)
    
    condition = or_(
        models.Link.last_accessed < one_week_ago,
        and_(
            models.Link.last_accessed.is_(None),
            models.Link.created_at < one_week_ago
        )
    )

    stmt = select(models.Link).where(condition)
    result = await db.execute(stmt)
    inactive_links = result.scalars().all()

    if inactive_links:
        await db.execute(
            delete(models.Link).where(
                models.Link.link_id.in_([link.link_id for link in inactive_links])
            )
        )
        await db.commit()
    
    return {"deleted_count": len(inactive_links)}

async def count_clicks_in_cache(db: AsyncSession, short_code: str):
    await db.execute(
        update(models.Link)
        .where(models.Link.short_code == short_code)
        .values(click_count=models.Link.click_count + 1)
    )
    await db.commit()
    
    return {"added click from cache": short_code}
