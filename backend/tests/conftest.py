"""Shared pytest fixtures: isolated test database + async HTTP client.

Every test runs against ``shipit_test`` with all tables recreated, so dev
data in the main ``shipit`` database is never touched.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401  (register all models on Base.metadata)
from app.database import Base
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:22058@localhost:5432/shipit_test"

test_engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def _override_get_session():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def _prepare_db():
    from app.dependencies import get_session

    app.dependency_overrides[get_session] = _override_get_session
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient) -> str:
    """Register a sender and return a valid JWT."""
    resp = await client.post(
        "/api/auth/register/sender",
        json={
            "name": "Test Sender",
            "email": "sender@example.com",
            "password": "password123",
            "phone": "+919999999999",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def driver_token(client: AsyncClient) -> str:
    """Register a driver and return a valid JWT."""
    resp = await client.post(
        "/api/auth/register/driver",
        json={
            "name": "Test Driver",
            "email": "driver@example.com",
            "password": "password123",
            "phone": "+919888888888",
            "vehicle_type": "van",
            "capacity_kg": 500,
            "license_number": "DL-01-2025-000001",
            "vehicle_reg_number": "MH12AB1234",
            "current_city": "Mumbai",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]
