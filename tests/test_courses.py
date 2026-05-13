import pytest
from httpx import AsyncClient


COURSE_DATA = {
    "title": "Python for Beginners",
    "description": "Learn Python from scratch",
    "level": "beginner",
    "price": 0.0,
    "tags": "python,programming",
}


@pytest.mark.asyncio
async def test_create_course_as_instructor(test_client: AsyncClient, instructor_headers):
    response = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == COURSE_DATA["title"]
    assert data["is_published"] is False
    return data


@pytest.mark.asyncio
async def test_create_course_as_student_forbidden(test_client: AsyncClient, student_headers):
    response = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=student_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_course_unauthenticated(test_client: AsyncClient):
    response = await test_client.post("/api/v1/courses", json=COURSE_DATA)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_courses(test_client: AsyncClient):
    response = await test_client.get("/api/v1/courses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_course(test_client: AsyncClient, instructor_headers):
    create_resp = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    course_id = create_resp.json()["id"]

    response = await test_client.get(f"/api/v1/courses/{course_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == course_id
    assert data["title"] == COURSE_DATA["title"]
    assert "instructor" in data


@pytest.mark.asyncio
async def test_get_course_not_found(test_client: AsyncClient):
    response = await test_client.get("/api/v1/courses/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_course_as_instructor(test_client: AsyncClient, instructor_headers):
    create_resp = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    course_id = create_resp.json()["id"]

    response = await test_client.put(
        f"/api/v1/courses/{course_id}",
        json={"title": "Updated Title", "price": 29.99},
        headers=instructor_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["price"] == 29.99


@pytest.mark.asyncio
async def test_update_course_other_instructor_forbidden(
    test_client: AsyncClient, instructor_headers, db_session
):
    create_resp = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    course_id = create_resp.json()["id"]

    from tests.conftest import _unique_suffix, create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    uid = _unique_suffix()
    other_instructor = await create_user_in_db(
        db_session,
        email=f"otherinstructor_{uid}@test.com",
        username=f"otherinstructor_{uid}",
        full_name="Other Instructor",
        role=UserRole.instructor,
    )
    other_headers = await get_auth_headers(test_client, other_instructor.email)

    response = await test_client.put(
        f"/api/v1/courses/{course_id}",
        json={"title": "Hacked Title"},
        headers=other_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_publish_course(test_client: AsyncClient, instructor_headers):
    create_resp = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    course_id = create_resp.json()["id"]
    assert create_resp.json()["is_published"] is False

    response = await test_client.post(
        f"/api/v1/courses/{course_id}/publish",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_published"] is True


@pytest.mark.asyncio
async def test_unpublish_course(test_client: AsyncClient, instructor_headers):
    create_resp = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    course_id = create_resp.json()["id"]

    await test_client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)

    response = await test_client.post(
        f"/api/v1/courses/{course_id}/unpublish",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_published"] is False


@pytest.mark.asyncio
async def test_delete_course_as_instructor(test_client: AsyncClient, instructor_headers):
    create_resp = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    course_id = create_resp.json()["id"]

    response = await test_client.delete(
        f"/api/v1/courses/{course_id}",
        headers=instructor_headers,
    )
    assert response.status_code == 204

    get_resp = await test_client.get(f"/api/v1/courses/{course_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_course_negative_price(test_client: AsyncClient, instructor_headers):
    response = await test_client.post(
        "/api/v1/courses",
        json={**COURSE_DATA, "price": -10.0},
        headers=instructor_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_can_update_any_course(test_client: AsyncClient, instructor_headers, admin_headers):
    create_resp = await test_client.post(
        "/api/v1/courses",
        json=COURSE_DATA,
        headers=instructor_headers,
    )
    course_id = create_resp.json()["id"]

    response = await test_client.put(
        f"/api/v1/courses/{course_id}",
        json={"title": "Admin Updated Title"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Admin Updated Title"
