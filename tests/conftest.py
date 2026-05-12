import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

# Override DATABASE_URL before any app imports so create_async_engine uses SQLite
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app
from app.models.user import UserRole
from app.services.auth import get_password_hash

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def create_user_in_db(
    session: AsyncSession,
    email: str,
    username: str,
    full_name: str,
    role: UserRole,
    password: str = "testpassword123",
) -> Any:
    from app.models.user import User

    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


@pytest_asyncio.fixture
async def test_student(db_session: AsyncSession) -> Any:
    suffix = _unique_suffix()
    return await create_user_in_db(
        db_session,
        email=f"student_{suffix}@test.com",
        username=f"student_{suffix}",
        full_name="Test Student",
        role=UserRole.student,
    )


@pytest_asyncio.fixture
async def test_instructor(db_session: AsyncSession) -> Any:
    suffix = _unique_suffix()
    return await create_user_in_db(
        db_session,
        email=f"instructor_{suffix}@test.com",
        username=f"instructor_{suffix}",
        full_name="Test Instructor",
        role=UserRole.instructor,
    )


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> Any:
    suffix = _unique_suffix()
    return await create_user_in_db(
        db_session,
        email=f"admin_{suffix}@test.com",
        username=f"admin_{suffix}",
        full_name="Test Admin",
        role=UserRole.admin,
    )


async def get_auth_headers(client: AsyncClient, email: str, password: str = "testpassword123") -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def student_headers(test_client: AsyncClient, test_student: Any) -> dict:
    return await get_auth_headers(test_client, test_student.email)


@pytest_asyncio.fixture
async def instructor_headers(test_client: AsyncClient, test_instructor: Any) -> dict:
    return await get_auth_headers(test_client, test_instructor.email)


@pytest_asyncio.fixture
async def admin_headers(test_client: AsyncClient, test_admin: Any) -> dict:
    return await get_auth_headers(test_client, test_admin.email)
