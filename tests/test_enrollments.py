import pytest
from httpx import AsyncClient


async def create_published_course(client: AsyncClient, instructor_headers: dict) -> int:
    resp = await client.post(
        "/api/v1/courses",
        json={
            "title": "Enrollment Test Course",
            "description": "For enrollment tests",
            "level": "beginner",
            "price": 0.0,
            "tags": "",
        },
        headers=instructor_headers,
    )
    course_id = resp.json()["id"]
    await client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    return course_id


@pytest.mark.asyncio
async def test_enroll_in_published_course(
    test_client: AsyncClient, student_headers, instructor_headers, db_session
):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    instr = await create_user_in_db(
        db_session, "enroll_instr@test.com", "enroll_instr", "Enroll Instructor", UserRole.instructor
    )
    instr_headers = await get_auth_headers(test_client, instr.email)
    course_id = await create_published_course(test_client, instr_headers)

    student = await create_user_in_db(
        db_session, "enroll_student@test.com", "enroll_student", "Enroll Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    response = await test_client.post(
        "/api/v1/enrollments",
        json={"course_id": course_id},
        headers=s_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["course_id"] == course_id
    assert data["progress"] == 0.0
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_enroll_in_unpublished_course(
    test_client: AsyncClient, db_session
):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    instr = await create_user_in_db(
        db_session, "unpub_instr@test.com", "unpub_instr", "Unpub Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)
    resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Unpublished", "description": "Not published", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instr_h,
    )
    course_id = resp.json()["id"]

    student = await create_user_in_db(
        db_session, "unpub_student@test.com", "unpub_student", "Unpub Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    response = await test_client.post(
        "/api/v1/enrollments",
        json={"course_id": course_id},
        headers=s_headers,
    )
    assert response.status_code == 400
    assert "unpublished" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_enrollment(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    instr = await create_user_in_db(
        db_session, "dup_instr@test.com", "dup_instr", "Dup Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)
    course_id = await create_published_course(test_client, instr_h)

    student = await create_user_in_db(
        db_session, "dup_student@test.com", "dup_student", "Dup Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    await test_client.post("/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers)
    response = await test_client.post(
        "/api/v1/enrollments",
        json={"course_id": course_id},
        headers=s_headers,
    )
    assert response.status_code == 400
    assert "Already enrolled" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_my_enrollments(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    instr = await create_user_in_db(
        db_session, "my_enroll_instr@test.com", "my_enroll_instr", "MyEnroll Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)
    course_id = await create_published_course(test_client, instr_h)

    student = await create_user_in_db(
        db_session, "my_enroll_student@test.com", "my_enroll_student", "MyEnroll Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    await test_client.post("/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers)

    response = await test_client.get("/api/v1/enrollments/my", headers=s_headers)
    assert response.status_code == 200
    enrollments = response.json()
    assert len(enrollments) >= 1
    assert any(e["course_id"] == course_id for e in enrollments)


@pytest.mark.asyncio
async def test_update_progress(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    instr = await create_user_in_db(
        db_session, "prog_instr@test.com", "prog_instr", "Prog Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)
    course_id = await create_published_course(test_client, instr_h)

    student = await create_user_in_db(
        db_session, "prog_student@test.com", "prog_student", "Prog Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    enroll_resp = await test_client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers
    )
    enrollment_id = enroll_resp.json()["id"]

    response = await test_client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 50.0},
        headers=s_headers,
    )
    assert response.status_code == 200
    assert response.json()["progress"] == 50.0


@pytest.mark.asyncio
async def test_complete_course_issues_certificate(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    instr = await create_user_in_db(
        db_session, "comp_instr@test.com", "comp_instr", "Comp Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)
    course_id = await create_published_course(test_client, instr_h)

    student = await create_user_in_db(
        db_session, "comp_student@test.com", "comp_student", "Comp Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    enroll_resp = await test_client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers
    )
    enrollment_id = enroll_resp.json()["id"]

    progress_resp = await test_client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 100.0},
        headers=s_headers,
    )
    assert progress_resp.status_code == 200
    assert progress_resp.json()["completed_at"] is not None

    cert_resp = await test_client.get("/api/v1/certificates/my", headers=s_headers)
    assert cert_resp.status_code == 200
    certs = cert_resp.json()
    assert len(certs) >= 1
    assert any(c["course_id"] == course_id for c in certs)


@pytest.mark.asyncio
async def test_progress_out_of_range(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole
    instr = await create_user_in_db(
        db_session, "range_instr@test.com", "range_instr", "Range Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)
    course_id = await create_published_course(test_client, instr_h)

    student = await create_user_in_db(
        db_session, "range_student@test.com", "range_student", "Range Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    enroll_resp = await test_client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers
    )
    enrollment_id = enroll_resp.json()["id"]

    response = await test_client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 150.0},
        headers=s_headers,
    )
    assert response.status_code == 422
