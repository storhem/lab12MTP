import uuid
import pytest
from httpx import AsyncClient


def uid() -> str:
    return uuid.uuid4().hex[:8]


async def setup_data(client: AsyncClient, db_session) -> tuple:
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    s = uid()
    instr = await create_user_in_db(
        db_session, f"an_instr_{s}@test.com", f"an_instr_{s}", "Analytics Instructor", UserRole.instructor
    )
    instr_h = await get_auth_headers(client, instr.email)

    student = await create_user_in_db(
        db_session, f"an_stu_{s}@test.com", f"an_stu_{s}", "Analytics Student", UserRole.student
    )
    s_headers = await get_auth_headers(client, student.email)

    admin = await create_user_in_db(
        db_session, f"an_admin_{s}@test.com", f"an_admin_{s}", "Analytics Admin", UserRole.admin
    )
    admin_h = await get_auth_headers(client, admin.email)

    course_resp = await client.post(
        "/api/v1/courses",
        json={"title": f"Analytics Course {s}", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instr_h,
    )
    course_id = course_resp.json()["id"]
    await client.post(f"/api/v1/courses/{course_id}/publish", headers=instr_h)

    enroll_resp = await client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers
    )
    enrollment_id = enroll_resp.json()["id"]

    await client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 75.0},
        headers=s_headers,
    )

    return instr_h, s_headers, admin_h, student, course_id


@pytest.mark.asyncio
async def test_top_courses_public(test_client: AsyncClient, db_session):
    await setup_data(test_client, db_session)
    response = await test_client.get("/api/v1/analytics/top-courses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "course_id" in data[0]
        assert "title" in data[0]
        assert "enrollment_count" in data[0]
        assert "avg_progress" in data[0]


@pytest.mark.asyncio
async def test_top_courses_with_limit(test_client: AsyncClient):
    response = await test_client.get("/api/v1/analytics/top-courses?limit=5")
    assert response.status_code == 200
    assert len(response.json()) <= 5


@pytest.mark.asyncio
async def test_student_progress_own(test_client: AsyncClient, db_session):
    instr_h, s_h, admin_h, student, course_id = await setup_data(test_client, db_session)

    response = await test_client.get(
        f"/api/v1/analytics/student/{student.id}/progress",
        headers=s_h,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == student.id
    assert "total_enrollments" in data
    assert "completed_courses" in data
    assert "avg_progress" in data
    assert "certificates_earned" in data


@pytest.mark.asyncio
async def test_student_progress_admin_can_view_any(test_client: AsyncClient, db_session):
    instr_h, s_h, admin_h, student, course_id = await setup_data(test_client, db_session)

    response = await test_client.get(
        f"/api/v1/analytics/student/{student.id}/progress",
        headers=admin_h,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_student_progress_forbidden_for_others(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    instr_h, s_h, admin_h, student, course_id = await setup_data(test_client, db_session)

    s2 = uid()
    other = await create_user_in_db(
        db_session, f"other_an_{s2}@test.com", f"other_an_{s2}", "Other", UserRole.student
    )
    other_h = await get_auth_headers(test_client, other.email)

    response = await test_client.get(
        f"/api/v1/analytics/student/{student.id}/progress",
        headers=other_h,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_platform_overview_admin_only(test_client: AsyncClient, db_session):
    instr_h, s_h, admin_h, student, course_id = await setup_data(test_client, db_session)

    response = await test_client.get(
        "/api/v1/analytics/overview",
        headers=admin_h,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_courses" in data
    assert "published_courses" in data
    assert "total_enrollments" in data
    assert "total_certificates_issued" in data
    assert "quiz_pass_rate" in data


@pytest.mark.asyncio
async def test_platform_overview_student_forbidden(test_client: AsyncClient, db_session):
    instr_h, s_h, admin_h, student, course_id = await setup_data(test_client, db_session)

    response = await test_client.get(
        "/api/v1/analytics/overview",
        headers=s_h,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_platform_overview_instructor_forbidden(test_client: AsyncClient, db_session):
    instr_h, s_h, admin_h, student, course_id = await setup_data(test_client, db_session)

    response = await test_client.get(
        "/api/v1/analytics/overview",
        headers=instr_h,
    )
    assert response.status_code == 403
