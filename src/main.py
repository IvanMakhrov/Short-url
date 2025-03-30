from fastapi import FastAPI, Depends
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from src.auth.users import auth_backend, current_active_user, fastapi_users
from src.auth.schemas import UserCreate, UserRead
from src.auth.db import User
from src.short_url.router import router as short_url_router
from src.database import async_session_maker
from src.short_url.crud import delete_expired_links, delete_inactive_links
import asyncio
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from src.config import settings

import uvicorn


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    asyncio.create_task(run_background_task())
    #redis = aioredis.from_url("redis://localhost")
    redis = aioredis.from_url(settings.REDIS_URL)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    app.state.redis = redis
    yield
    await FastAPICache.clear()
    await redis.aclose()


async def run_background_task():
    while True:
        async with async_session_maker() as session:
            await delete_expired_links(session)
            await delete_inactive_links(session)
        await asyncio.sleep(86400)


app = FastAPI(lifespan=lifespan)


app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(short_url_router)


@app.get("/protected-route")
def protected_route(user: User = Depends(current_active_user)):
    return f"Hello, {user.email}"


@app.get("/unprotected-route")
def unprotected_route():
    return f"Hello, anonym"


#if __name__ == "__main__":
#    uvicorn.run("main:app", reload=True, host="0.0.0.0", log_level="info")
