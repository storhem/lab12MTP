import pytest
from httpx import AsyncClient


LESSON_DATA = {
    "title": "Introduction to Python",
    "content": "Python is a high-level programming language...",
    "order_num": 1,
    "duration_minutes": 30,
    "is_published": True,
}


async def create_test_course(client: AsyncClient, headers: dict) -> int:
    resp = await client.post(
        "/api/v1/courses",
        json={
            "title": "Test Course",
            "description": "Test Description",
            "level": "beginner",
            "price": 0.0,
            "tags": "",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_add_lesson_to_course(test_client: AsyncClient, instructor_headers):
    course_id = await create_test_course(test_client, instructor_headers)

    response = await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json=LESSON_DATA,
        headers=instructor_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == LESSON_DATA["title"]
    assert data["course_id"] == course_id
    assert data["order_num"] == LESSON_DATA["order_num"]


@pytest.mark.asyncio
async def test_add_lesson_to_nonexistent_course(test_client: AsyncClient, instructor_headers):
    response = await test_client.post(
        "/api/v1/lessons/course/999999",
        json=LESSON_DATA,
        headers=instructor_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_lesson_as_student_forbidden(test_client: AsyncClient, instructor_headers, student_headers):
    course_id = await create_test_course(test_client, instructor_headers)

    response = await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json=LESSON_DATA,
        headers=student_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_lessons(test_client: AsyncClient, instructor_headers):
    course_id = await create_test_course(test_client, instructor_headers)

    for i in range(3):
        await test_client.post(
            f"/api/v1/lessons/course/{course_id}",
            json={**LESSON_DATA, "title": f"Lesson {i+1}", "order_num": i + 1},
            headers=instructor_headers,
        )

    response = await test_client.get(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    lessons = response.json()
    assert len(lessons) >= 3


@pytest.mark.asyncio
async def test_get_lesson(test_client: AsyncClient, instructor_headers):
    course_id = await create_test_course(test_client, instructor_headers)

    create_resp = await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json=LESSON_DATA,
        headers=instructor_headers,
    )
    lesson_id = create_resp.json()["id"]

    response = await test_client.get(
        f"/api/v1/lessons/{lesson_id}",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == lesson_id


@pytest.mark.asyncio
async def test_update_lesson(test_client: AsyncClient, instructor_headers):
    course_id = await create_test_course(test_client, instructor_headers)

    create_resp = await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json=LESSON_DATA,
        headers=instructor_headers,
    )
    lesson_id = create_resp.json()["id"]

    response = await test_client.put(
        f"/api/v1/lessons/{lesson_id}",
        json={"title": "Updated Lesson", "duration_minutes": 45},
        headers=instructor_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Lesson"
    assert data["duration_minutes"] == 45


@pytest.mark.asyncio
async def test_delete_lesson(test_client: AsyncClient, instructor_headers):
    course_id = await create_test_course(test_client, instructor_headers)

    create_resp = await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json=LESSON_DATA,
        headers=instructor_headers,
    )
    lesson_id = create_resp.json()["id"]

    response = await test_client.delete(
        f"/api/v1/lessons/{lesson_id}",
        headers=instructor_headers,
    )
    assert response.status_code == 204

    get_resp = await test_client.get(
        f"/api/v1/lessons/{lesson_id}",
        headers=instructor_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_lesson_order(test_client: AsyncClient, instructor_headers):
    course_id = await create_test_course(test_client, instructor_headers)

    for order in [3, 1, 2]:
        await test_client.post(
            f"/api/v1/lessons/course/{course_id}",
            json={**LESSON_DATA, "title": f"Lesson {order}", "order_num": order},
            headers=instructor_headers,
        )

    response = await test_client.get(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
    )
    lessons = response.json()
    order_nums = [l["order_num"] for l in lessons]
    assert order_nums == sorted(order_nums)


@pytest.mark.asyncio
async def test_update_lesson_not_found(test_client: AsyncClient, instructor_headers):
    response = await test_client.put(
        "/api/v1/lessons/999999",
        json={"title": "Ghost Lesson"},
        headers=instructor_headers,
    )
    assert response.status_code == 404
