import os
import sys
import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.auth.db import User
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(scope="session")
async def test_db_setup():
    from src.database import Base, engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_db_setup):
    from src.database import async_session_maker
    async with async_session_maker() as session:
        yield session
        await session.rollback()

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_current_user(mocker):
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    mocker.patch("src.auth.users.current_active_user", return_value=user)
    mocker.patch("src.auth.users.current_active_user_optional", return_value=user)
