import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(test_client: AsyncClient):
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "role": "student",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert data["role"] == "student"
    assert "hashed_password" not in data
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client: AsyncClient, test_student):
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": test_student.email,
            "username": "anotheruser",
            "full_name": "Another User",
            "role": "student",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username(test_client: AsyncClient, test_student):
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "different@example.com",
            "username": test_student.username,
            "full_name": "Another User",
            "role": "student",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, test_student):
    response = await test_client.post(
        "/api/v1/auth/login",
        json={"email": test_student.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(test_client: AsyncClient, test_student):
    response = await test_client.post(
        "/api/v1/auth/login",
        json={"email": test_student.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_email(test_client: AsyncClient):
    response = await test_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(test_client: AsyncClient, student_headers, test_student):
    response = await test_client.get("/api/v1/auth/me", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_student.email
    assert data["username"] == test_student.username


@pytest.mark.asyncio
async def test_get_me_unauthenticated(test_client: AsyncClient):
    response = await test_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(test_client: AsyncClient):
    response = await test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_instructor(test_client: AsyncClient):
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newinstructor@example.com",
            "username": "newinstructor",
            "full_name": "New Instructor",
            "role": "instructor",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "instructor"


@pytest.mark.asyncio
async def test_register_short_password(test_client: AsyncClient):
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpwd@example.com",
            "username": "shortpwd",
            "full_name": "Short Pwd",
            "role": "student",
            "password": "abc",
        },
    )
    assert response.status_code == 422
