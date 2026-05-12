import pytest
from httpx import AsyncClient


async def setup_completed_enrollment(client: AsyncClient, db_session) -> tuple[int, dict]:
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    instr = await create_user_in_db(
        db_session,
        f"cert_instr_{id(db_session)}@test.com",
        f"cert_instr_{id(db_session)}",
        "Cert Instructor",
        UserRole.instructor,
    )
    instr_h = await get_auth_headers(client, instr.email)

    course_resp = await client.post(
        "/api/v1/courses",
        json={"title": "Cert Course", "description": "Cert desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instr_h,
    )
    course_id = course_resp.json()["id"]
    await client.post(f"/api/v1/courses/{course_id}/publish", headers=instr_h)

    student = await create_user_in_db(
        db_session,
        f"cert_student_{id(db_session)}@test.com",
        f"cert_student_{id(db_session)}",
        "Cert Student",
        UserRole.student,
    )
    s_headers = await get_auth_headers(client, student.email)

    enroll_resp = await client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers
    )
    enrollment_id = enroll_resp.json()["id"]

    await client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 100.0},
        headers=s_headers,
    )

    return course_id, s_headers


@pytest.mark.asyncio
async def test_certificate_issued_on_completion(test_client: AsyncClient, db_session):
    course_id, s_headers = await setup_completed_enrollment(test_client, db_session)

    response = await test_client.get("/api/v1/certificates/my", headers=s_headers)
    assert response.status_code == 200
    certs = response.json()
    assert len(certs) >= 1
    cert = next((c for c in certs if c["course_id"] == course_id), None)
    assert cert is not None
    assert "certificate_number" in cert
    assert cert["certificate_number"].startswith("CERT-")


@pytest.mark.asyncio
async def test_verify_certificate_valid(test_client: AsyncClient, db_session):
    course_id, s_headers = await setup_completed_enrollment(test_client, db_session)

    certs_resp = await test_client.get("/api/v1/certificates/my", headers=s_headers)
    cert = certs_resp.json()[0]
    cert_number = cert["certificate_number"]

    response = await test_client.get(f"/api/v1/certificates/{cert_number}/verify")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["certificate_number"] == cert_number
    assert "student_full_name" in data
    assert "course_title" in data
    assert "issued_at" in data


@pytest.mark.asyncio
async def test_verify_certificate_invalid(test_client: AsyncClient):
    response = await test_client.get("/api/v1/certificates/CERT-NONEXISTENT/verify")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_certificates_empty(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    student = await create_user_in_db(
        db_session,
        "nocerts@test.com",
        "nocertstudent",
        "No Certs Student",
        UserRole.student,
    )
    s_headers = await get_auth_headers(test_client, student.email)

    response = await test_client.get("/api/v1/certificates/my", headers=s_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_certificate_not_duplicated_on_second_completion(test_client: AsyncClient, db_session):
    from tests.conftest import create_user_in_db, get_auth_headers
    from app.models.user import UserRole

    instr = await create_user_in_db(
        db_session, "nodup_instr@test.com", "nodup_instr", "NoDup Instr", UserRole.instructor
    )
    instr_h = await get_auth_headers(test_client, instr.email)

    course_resp = await test_client.post(
        "/api/v1/courses",
        json={"title": "NoDup Course", "description": "desc", "level": "beginner", "price": 0.0, "tags": ""},
        headers=instr_h,
    )
    course_id = course_resp.json()["id"]
    await test_client.post(f"/api/v1/courses/{course_id}/publish", headers=instr_h)

    student = await create_user_in_db(
        db_session, "nodup_student@test.com", "nodup_student", "NoDup Student", UserRole.student
    )
    s_headers = await get_auth_headers(test_client, student.email)

    enroll_resp = await test_client.post(
        "/api/v1/enrollments", json={"course_id": course_id}, headers=s_headers
    )
    enrollment_id = enroll_resp.json()["id"]

    await test_client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 100.0},
        headers=s_headers,
    )
    await test_client.put(
        f"/api/v1/enrollments/{enrollment_id}/progress",
        json={"progress": 100.0},
        headers=s_headers,
    )

    certs_resp = await test_client.get("/api/v1/certificates/my", headers=s_headers)
    certs = [c for c in certs_resp.json() if c["course_id"] == course_id]
    assert len(certs) == 1


@pytest.mark.asyncio
async def test_get_my_certificates_unauthenticated(test_client: AsyncClient):
    response = await test_client.get("/api/v1/certificates/my")
    assert response.status_code == 401
