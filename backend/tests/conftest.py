"""
Pytest configuration and fixtures for Digital Bank backend tests.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.config import settings


# Use a separate test database
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "sqlite+aiosqlite:///./bank.db",
    "sqlite+aiosqlite:///./test_bank.db"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database for each test function."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test."""
    yield test_db
    await test_db.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Create a registered user for testing."""
    user_data = {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "phone": "+1234567890"
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    return {
        "user": data,
        "credentials": {"email": user_data["email"], "password": user_data["password"]}
    }


@pytest_asyncio.fixture
async def admin_user(client: AsyncClient) -> dict:
    """Create an admin user for testing."""
    user_data = {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin User",
        "phone": "+1234567890",
        "role": "admin"
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    return {
        "user": data,
        "credentials": {"email": user_data["email"], "password": user_data["password"]}
    }


@pytest_asyncio.fixture
async def authenticated_user(client: AsyncClient, registered_user: dict) -> dict:
    """Get an authenticated user with login token."""
    response = await client.post(
        "/api/v1/auth/login",
        json=registered_user["credentials"]
    )
    assert response.status_code == 200
    tokens = response.json()
    return {
        "user": registered_user["user"],
        "tokens": tokens,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


@pytest_asyncio.fixture
async def authenticated_admin(client: AsyncClient, admin_user: dict) -> dict:
    """Get an authenticated admin with login token."""
    response = await client.post(
        "/api/v1/auth/login",
        json=admin_user["credentials"]
    )
    assert response.status_code == 200
    tokens = response.json()
    return {
        "user": admin_user["user"],
        "tokens": tokens,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


@pytest_asyncio.fixture
async def user_account(client: AsyncClient, authenticated_user: dict) -> dict:
    """Create a bank account for the authenticated user."""
    response = await client.post(
        "/api/v1/accounts",
        json={
            "account_type": "savings",
            "currency": "USD"
        },
        headers=authenticated_user["headers"]
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def second_account(client: AsyncClient) -> dict:
    """Create a second user with account for transfer tests."""
    user_data = {
        "email": "seconduser@example.com",
        "password": "SecondPass123!",
        "full_name": "Second User",
        "phone": "+0987654321"
    }
    await client.post("/api/v1/auth/register", json=user_data)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]}
    )
    tokens = login_resp.json()

    account_resp = await client.post(
        "/api/v1/accounts",
        json={"account_type": "checking", "currency": "USD"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    return account_resp.json()
