from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.short_url.schemas import LinkCreate
from fastapi.responses import RedirectResponse
from fastapi import Security
from fastapi.security import HTTPBearer
import src.short_url.crud as crud
from typing import Optional
import datetime
from src.short_url.cache import cache_link, get_cached_link, clear_cached_link, cache_stats, get_cached_stats, cache_search_result, get_cached_search
from src.auth.users import current_active_user, current_active_user_optional
from src.auth.db import User


router = APIRouter(
    prefix="/links",
    tags=["links"]
)

security = HTTPBearer(auto_error=False)

@router.post("/shorten")
async def create_short_link(
    link: LinkCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user_optional)
):

    if link.custom_alias:
        cached_link = await get_cached_link(link.custom_alias)
        if cached_link:
            raise HTTPException(status_code=400, detail="Custom alias already exists")
    
        #existing_link = await crud.get_link_by_short_code(session, link.custom_alias)
    db_link = await crud.create_link(session, link, user.id if user else None)
    if not db_link:
        raise HTTPException(status_code=400, detail="Custom alias already exists")
    
    base_url = str(request.base_url)
    shortened_url = f"{base_url}links/{db_link.short_code}"

    return {"short_code": shortened_url}


@router.get("/{short_code}")
async def redirect_to_original(short_code: str, session: AsyncSession = Depends(get_async_session)):
    cached_link = await get_cached_link(short_code)
    if cached_link:
        await crud.count_clicks_in_cache(session, short_code)
        return RedirectResponse(url=cached_link.original_url)
    
    link = await crud.get_link_by_short_code(session, short_code)
    if not link or (link.expires_at and link.expires_at < datetime.datetime.now()):
        raise HTTPException(status_code=404, detail="Link not found or expired")
    
    await crud.update_link_stats(session, link)
    await cache_link(link)
    
    return RedirectResponse(url=link.original_url)


@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
    ):
    
    link = await crud.get_link_by_short_code(session, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this link"
        )

    if not await crud.delete_link(session, short_code):
        raise HTTPException(status_code=404, detail="Link not found")
    
    await clear_cached_link(short_code)
    return {"message": "Link deleted"}


@router.put("/{short_code}")
async def update_link(
    short_code: str,
    new_url: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
    ):

    link = await crud.get_link_by_short_code(session, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this link"
        )
    
    result = await crud.update_link(session, short_code, new_url)

    if not result:
        raise HTTPException(status_code=404, detail="Link not found")
    
    await clear_cached_link(short_code)
    return {"message": "Link updated"}


@router.get("/{short_code}/stats")
async def get_link_stats(
    short_code: str,
    session: AsyncSession = Depends(get_async_session)
    ):

    cached_stats = await get_cached_stats(short_code)
    if cached_stats:
        return cached_stats
    
    stats = await crud.get_link_stats(session, short_code)
    if not stats:
        raise HTTPException(status_code=404, detail="Link not found")
    
    await cache_stats(short_code, stats)
    return stats

@router.get("/search/{original_url:path}")
async def search_link(
    original_url: str,
    session: AsyncSession = Depends(get_async_session)
    ):

    cached_link = await get_cached_search(original_url)
    if cached_link:
        return cached_link

    link = await crud.search_link_by_url(session, original_url)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    await cache_search_result(original_url, link)
    return link

@router.patch("/{short_code}/expiration")
async def update_link_expiration(
    short_code: str,
    expires_at: Optional[datetime.datetime] = None,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
    ):
    
    link = await crud.get_link_by_short_code(session, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this link"
        )
    
    link.expires_at = expires_at
    await session.commit()
    await session.refresh(link)
    
    return {"message": "Expiration updated", "expires_at": link.expires_at}
