import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_login_form_endpoint(test_client: AsyncClient, test_student):
    response = await test_client.post(
        "/api/v1/auth/login/form",
        data={"username": test_student.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(test_client: AsyncClient):
    response = await test_client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_list_all_courses_instructor(test_client: AsyncClient, instructor_headers):
    await test_client.post(
        "/api/v1/courses",
        json={"title": "Unpublished Extra", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    response = await test_client.get("/api/v1/courses/all", headers=instructor_headers)
    assert response.status_code == 200
    courses = response.json()
    assert isinstance(courses, list)


@pytest.mark.asyncio
async def test_get_course_students(test_client: AsyncClient, instructor_headers, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Students Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]
    await test_client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)

    student = await create_user_in_db(
        db_session, "stu_for_course@test.com", "stu_for_course", "Stu Course", UserRole.student
    )
    s_h = await get_auth_headers(test_client, student.email)
    await test_client.post("/api/v1/enrollments", json={"course_id": course_id}, headers=s_h)

    response = await test_client.get(
        f"/api/v1/courses/{course_id}/students",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_course_invalid_level(test_client: AsyncClient, instructor_headers):
    response = await test_client.post(
        "/api/v1/courses",
        json={"title": "Bad Level", "description": "desc", "level": "expert", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_enroll_nonexistent_course(test_client: AsyncClient, student_headers):
    response = await test_client.post(
        "/api/v1/enrollments",
        json={"course_id": 999999},
        headers=student_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_progress_wrong_enrollment(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    instr = await create_user_in_db(
        db_session, "perm_instr@test.com", "perm_instr", "Perm Instructor", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)

    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Permission Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instr_h,
    )
    course_id = course_resp.json()["id"]
    await test_client.post(f"/api/v1/courses/{course_id}/publish", headers=instr_h)

    student1 = await create_user_in_db(
        db_session, "perm_stu1@test.com", "perm_stu1", "Perm Student 1", UserRole.student
    )
    s1_h = await get_auth_headers(test_client, student1.email)

    student2 = await create_user_in_db(
        db_session, "perm_stu2@test.com", "perm_stu2", "Perm Student 2", UserRole.student
    )
    s2_h = await get_auth_headers(test_client, student2.email)

    enroll_resp = await test_client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s1_h
    )
    enrollment_id = enroll_resp.json()["id"]

    response = await test_client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 50.0},
        headers=s2_h,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_quiz_attempt_instructor_forbidden(test_client: AsyncClient, instructor_headers, db_session):
    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Instr Quiz Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    quiz_resp = await test_client.post(
        "/api/v1/quizzes",
        json={"course_id": course_id, "title": "Instr Quiz", "questions": [], "passing_score": 70},
        headers=instructor_headers,
    )
    quiz_id = quiz_resp.json()["id"]

    response = await test_client.post(
        f"/api/v1/quizzes/{quiz_id}/attempt",
        json={"answers": []},
        headers=instructor_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_quiz_list_by_course(test_client: AsyncClient, instructor_headers):
    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Quiz List Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    for i in range(3):
        await test_client.post(
            "/api/v1/quizzes",
            json={"course_id": course_id, "title": f"Quiz {i}", "questions": [], "passing_score": 70},
            headers=instructor_headers,
        )

    response = await test_client.get(
        f"/api/v1/quizzes/course/{course_id}",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 3


@pytest.mark.asyncio
async def test_quiz_empty_questions_score(test_client: AsyncClient, instructor_headers, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Empty Q Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    quiz_resp = await test_client.post(
        "/api/v1/quizzes",
        json={"course_id": course_id, "title": "Empty Quiz", "questions": [], "passing_score": 70},
        headers=instructor_headers,
    )
    quiz_id = quiz_resp.json()["id"]

    student = await create_user_in_db(
        db_session, "empty_quiz_stu@test.com", "empty_quiz_stu", "Empty Quiz Student", UserRole.student
    )
    s_h = await get_auth_headers(test_client, student.email)

    response = await test_client.post(
        f"/api/v1/quizzes/{quiz_id}/attempt",
        json={"answers": []},
        headers=s_h,
    )
    assert response.status_code == 201
    assert response.json()["score"] == 0.0
    assert response.json()["passed"] is False


@pytest.mark.asyncio
async def test_quiz_with_lesson_id(test_client: AsyncClient, instructor_headers):
    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Lesson Quiz Course", "description": "desc", "level": "intermediate", "price": 9.99, "tags": "test"},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    lesson_resp = await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json={"title": "Lesson 1", "content": "Content", "order_num": 1, "duration_minutes": 10, "is_published": True},
        headers=instructor_headers,
    )
    lesson_id = lesson_resp.json()["id"]

    quiz_resp = await test_client.post(
        "/api/v1/quizzes",
        json={"course_id": course_id, "lesson_id": lesson_id, "title": "Lesson Quiz", "questions": [], "passing_score": 50},
        headers=instructor_headers,
    )
    assert quiz_resp.status_code == 201
    assert quiz_resp.json()["lesson_id"] == lesson_id


@pytest.mark.asyncio
async def test_verify_certificate_case_sensitive(test_client: AsyncClient, db_session):
    response = await test_client.get("/api/v1/certificates/cert-lowercase-12345/verify")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_inactive_enrollment(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    instr = await create_user_in_db(
        db_session, "inactive_instr@test.com", "inactive_instr", "Inactive Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)

    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Inactive Test Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instr_h,
    )
    course_id = course_resp.json()["id"]
    await test_client.post(f"/api/v1/courses/{course_id}/publish", headers=instr_h)

    student = await create_user_in_db(
        db_session, "inactive_stu@test.com", "inactive_stu", "Inactive Stu", UserRole.student
    )
    s_h = await get_auth_headers(test_client, student.email)

    enroll_resp = await test_client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s_h
    )
    enrollment_id = enroll_resp.json()["id"]

    prog_resp = await test_client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 50.0},
        headers=s_h,
    )
    assert prog_resp.status_code == 200


@pytest.mark.asyncio
async def test_instructor_can_see_unpublished_lessons(test_client: AsyncClient, instructor_headers):
    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Instr Lessons Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json={"title": "Published", "content": "...", "order_num": 1, "duration_minutes": 10, "is_published": True},
        headers=instructor_headers,
    )
    await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json={"title": "Unpublished", "content": "...", "order_num": 2, "duration_minutes": 10, "is_published": False},
        headers=instructor_headers,
    )

    response = await test_client.get(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    titles = [l["title"] for l in response.json()]
    assert "Published" in titles
    assert "Unpublished" in titles


@pytest.mark.asyncio
async def test_student_only_sees_published_lessons(test_client: AsyncClient, instructor_headers, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Student Lesson Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json={"title": "Visible", "content": "...", "order_num": 1, "duration_minutes": 10, "is_published": True},
        headers=instructor_headers,
    )
    await test_client.post(
        f"/api/v1/lessons/course/{course_id}",
        json={"title": "Hidden", "content": "...", "order_num": 2, "duration_minutes": 5, "is_published": False},
        headers=instructor_headers,
    )

    student = await create_user_in_db(
        db_session, "lesson_stu@test.com", "lesson_stu", "Lesson Student", UserRole.student
    )
    s_h = await get_auth_headers(test_client, student.email)

    response = await test_client.get(
        f"/api/v1/courses/{course_id}/lessons",
        headers=s_h,
    )
    assert response.status_code == 200
    titles = [l["title"] for l in response.json()]
    assert "Visible" in titles
    assert "Hidden" not in titles


@pytest.mark.asyncio
async def test_delete_nonexistent_lesson(test_client: AsyncClient, instructor_headers):
    response = await test_client.delete(
        "/api/v1/lessons/999999",
        headers=instructor_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_course_advanced_level(test_client: AsyncClient, instructor_headers):
    response = await test_client.post(
        "/api/v1/courses",
        json={"title": "Advanced Course", "description": "Advanced content", "level": "advanced", "price": 99.99, "tags": "advanced"},
        headers=instructor_headers,
    )
    assert response.status_code == 201
    assert response.json()["level"] == "advanced"
    assert response.json()["price"] == 99.99
