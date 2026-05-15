import pytest
from httpx import AsyncClient

from app.models.user import UserRole
from tests.conftest import create_user_in_db, get_auth_headers


QUESTIONS = [
    {
        "question": "What is 2 + 2?",
        "options": ["3", "4", "5", "6"],
        "correct_answer": "4",
    },
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "London", "Paris", "Rome"],
        "correct_answer": "Paris",
    },
    {
        "question": "Which language is used for web backend with FastAPI?",
        "options": ["JavaScript", "Python", "Java", "C#"],
        "correct_answer": "Python",
    },
]


async def create_course_and_quiz(client: AsyncClient, instr_headers: dict) -> tuple[int, int]:
    course_resp = await client.post(
        "/api/v1/courses",
        json={"title": "Quiz Test Course", "description": "For quizzes", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instr_headers,
    )
    course_id = course_resp.json()["id"]

    quiz_resp = await client.post(
        "/api/v1/quizzes",
        json={
            "course_id": course_id,
            "title": "Test Quiz",
            "questions": QUESTIONS,
            "passing_score": 70,
        },
        headers=instr_headers,
    )
    assert quiz_resp.status_code == 201
    quiz_id = quiz_resp.json()["id"]
    return course_id, quiz_id


@pytest.mark.asyncio
async def test_create_quiz(test_client: AsyncClient, instructor_headers):
    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "Quiz Course", "description": "Desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    response = await test_client.post(
        "/api/v1/quizzes",
        json={"course_id": course_id, "title": "My Quiz", "questions": QUESTIONS, "passing_score": 70},
        headers=instructor_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Quiz"
    assert data["passing_score"] == 70
    assert len(data["questions"]) == 3


@pytest.mark.asyncio
async def test_create_quiz_as_student_forbidden(test_client: AsyncClient, instructor_headers, student_headers):
    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "No Student Quiz", "description": "Desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instructor_headers,
    )
    course_id = course_resp.json()["id"]

    response = await test_client.post(
        "/api/v1/quizzes",
        json={"course_id": course_id, "title": "Forbidden Quiz", "questions": [], "passing_score": 70},
        headers=student_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_quiz(test_client: AsyncClient, instructor_headers):
    _, quiz_id = await create_course_and_quiz(test_client, instructor_headers)

    response = await test_client.get(f"/api/v1/quizzes/{quiz_id}", headers=instructor_headers)
    assert response.status_code == 200
    assert response.json()["id"] == quiz_id


@pytest.mark.asyncio
async def test_get_quiz_not_found(test_client: AsyncClient, instructor_headers):
    response = await test_client.get("/api/v1/quizzes/999999", headers=instructor_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_attempt_passing(test_client: AsyncClient, instructor_headers, db_session):

    _, quiz_id = await create_course_and_quiz(test_client, instructor_headers)

    student = await create_user_in_db(
        db_session, "quiz_pass_student@test.com", "quiz_pass_student", "Quiz Pass Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    correct_answers = ["4", "Paris", "Python"]
    response = await test_client.post(
        f"/api/v1/quizzes/{quiz_id}/attempt",
        json={"answers": correct_answers},
        headers=s_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["passed"] is True
    assert data["score"] == 100.0


@pytest.mark.asyncio
async def test_submit_attempt_failing(test_client: AsyncClient, instructor_headers, db_session):

    _, quiz_id = await create_course_and_quiz(test_client, instructor_headers)

    student = await create_user_in_db(
        db_session, "quiz_fail_student@test.com", "quiz_fail_student", "Quiz Fail Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    wrong_answers = ["3", "Berlin", "Java"]
    response = await test_client.post(
        f"/api/v1/quizzes/{quiz_id}/attempt",
        json={"answers": wrong_answers},
        headers=s_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["passed"] is False
    assert data["score"] == 0.0


@pytest.mark.asyncio
async def test_submit_attempt_partial_score(test_client: AsyncClient, instructor_headers, db_session):

    _, quiz_id = await create_course_and_quiz(test_client, instructor_headers)

    student = await create_user_in_db(
        db_session, "quiz_partial_student@test.com", "quiz_partial_student", "Partial Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    mixed_answers = ["4", "Berlin", "Python"]
    response = await test_client.post(
        f"/api/v1/quizzes/{quiz_id}/attempt",
        json={"answers": mixed_answers},
        headers=s_headers,
    )
    assert response.status_code == 201
    data = response.json()
    expected_score = (2 / 3) * 100
    assert abs(data["score"] - expected_score) < 0.01


@pytest.mark.asyncio
async def test_get_attempt_results(test_client: AsyncClient, instructor_headers, db_session):

    _, quiz_id = await create_course_and_quiz(test_client, instructor_headers)

    student = await create_user_in_db(
        db_session, "quiz_results_student@test.com", "quiz_results_student", "Results Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    await test_client.post(
        f"/api/v1/quizzes/{quiz_id}/attempt",
        json={"answers": ["4", "Paris", "Python"]},
        headers=s_headers,
    )

    response = await test_client.get(
        f"/api/v1/quizzes/{quiz_id}/results",
        headers=s_headers,
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert results[0]["quiz_id"] == quiz_id


@pytest.mark.asyncio
async def test_update_quiz(test_client: AsyncClient, instructor_headers):
    _, quiz_id = await create_course_and_quiz(test_client, instructor_headers)

    response = await test_client.put(
        f"/api/v1/quizzes/{quiz_id}",
        json={"title": "Updated Quiz Title", "passing_score": 80},
        headers=instructor_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Quiz Title"
    assert data["passing_score"] == 80


@pytest.mark.asyncio
async def test_delete_quiz(test_client: AsyncClient, instructor_headers):
    _, quiz_id = await create_course_and_quiz(test_client, instructor_headers)

    response = await test_client.delete(
        f"/api/v1/quizzes/{quiz_id}",
        headers=instructor_headers,
    )
    assert response.status_code == 204

    get_resp = await test_client.get(f"/api/v1/quizzes/{quiz_id}", headers=instructor_headers)
    assert get_resp.status_code == 404
