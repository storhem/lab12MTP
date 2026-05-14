import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.lesson import LessonCreate, LessonUpdate
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizAttemptCreate
from app.services import auth as auth_service
from app.services import courses as course_service
from app.services import lessons as lesson_service
from app.services import enrollments as enrollment_service
from app.services import quizzes as quiz_service
from app.services import certificates as cert_service
from app.services import analytics as analytics_service


def uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_auth_register_and_login(db_session: AsyncSession):
    s = uid()
    user_data = UserCreate(
        email=f"svc_{s}@test.com",
        username=f"svc_{s}",
        full_name="Service Test User",
        role=UserRole.student,
        password="securepassword123",
    )
    user = await auth_service.register(user_data, db_session)
    assert user.id is not None
    assert user.email == user_data.email

    token = await auth_service.login(user_data.email, "securepassword123", db_session)
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_auth_register_duplicate_email(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    user_data = UserCreate(
        email=f"dup_svc_{s}@test.com",
        username=f"dup_svc_{s}",
        full_name="Dup Test",
        role=UserRole.student,
        password="password123",
    )
    await auth_service.register(user_data, db_session)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register(user_data, db_session)
    assert exc_info.value.status_code == 400
    assert "Email already registered" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_auth_register_duplicate_username(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    user1 = UserCreate(
        email=f"uname1_{s}@test.com",
        username=f"uname_{s}",
        full_name="User 1",
        role=UserRole.student,
        password="password123",
    )
    user2 = UserCreate(
        email=f"uname2_{s}@test.com",
        username=f"uname_{s}",  # same username
        full_name="User 2",
        role=UserRole.student,
        password="password123",
    )
    await auth_service.register(user1, db_session)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register(user2, db_session)
    assert exc_info.value.status_code == 400
    assert "Username already taken" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_auth_login_wrong_password(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    user_data = UserCreate(
        email=f"wrongpwd_{s}@test.com",
        username=f"wrongpwd_{s}",
        full_name="Wrong Pwd",
        role=UserRole.student,
        password="correctpassword",
    )
    await auth_service.register(user_data, db_session)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login(user_data.email, "wrongpassword", db_session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_login_nonexistent_user(db_session: AsyncSession):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login("nobody@nowhere.com", "password", db_session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_courses_service_create_and_list(db_session: AsyncSession):
    s = uid()
    instructor = await auth_service.register(
        UserCreate(
            email=f"instr_svc_{s}@test.com",
            username=f"instr_svc_{s}",
            full_name="Instructor",
            role=UserRole.instructor,
            password="password123",
        ),
        db_session,
    )

    course_data = CourseCreate(
        title="Service Test Course",
        description="For direct service tests",
        level="beginner",
        price=0.0,
        tags="test",
    )
    course = await course_service.create_course(course_data, instructor, db_session)
    assert course.id is not None
    assert course.instructor_id == instructor.id
    assert course.is_published is False

    courses = await course_service.list_courses(
        skip=0, limit=100, published_only=False, session=db_session
    )
    assert any(c.id == course.id for c in courses)


@pytest.mark.asyncio
async def test_courses_service_update_and_publish(db_session: AsyncSession):
    s = uid()
    instructor = await auth_service.register(
        UserCreate(
            email=f"upd_instr_{s}@test.com",
            username=f"upd_instr_{s}",
            full_name="Update Instructor",
            role=UserRole.instructor,
            password="password123",
        ),
        db_session,
    )

    course = await course_service.create_course(
        CourseCreate(title="Updatable Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor,
        db_session,
    )

    updated = await course_service.update_course(
        course.id,
        CourseUpdate(title="Updated Course Title", price=19.99),
        instructor,
        db_session,
    )
    assert updated.title == "Updated Course Title"
    assert updated.price == 19.99

    published = await course_service.publish_course(course.id, instructor, db_session)
    assert published.is_published is True

    unpublished = await course_service.unpublish_course(course.id, instructor, db_session)
    assert unpublished.is_published is False


@pytest.mark.asyncio
async def test_courses_service_get_not_found(db_session: AsyncSession):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await course_service.get_course(999999, db_session)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_courses_service_update_forbidden(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"f_instr_{s}@test.com", username=f"f_instr_{s}",
                   full_name="F Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    other = await auth_service.register(
        UserCreate(email=f"f_other_{s}@test.com", username=f"f_other_{s}",
                   full_name="F Other", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="Forbidden Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    with pytest.raises(HTTPException) as exc_info:
        await course_service.update_course(course.id, CourseUpdate(title="Hack"), other, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_courses_service_delete(db_session: AsyncSession):
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"del_instr_{s}@test.com", username=f"del_instr_{s}",
                   full_name="Del Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="Delete Me", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    await course_service.delete_course(course.id, instructor, db_session)

    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        await course_service.get_course(course.id, db_session)


@pytest.mark.asyncio
async def test_lessons_service_add_list_update_delete(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"l_instr_{s}@test.com", username=f"l_instr_{s}",
                   full_name="L Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="Lesson Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    lesson = await lesson_service.add_lesson(
        course.id,
        LessonCreate(title="My Lesson", content="Content here", order_num=1, duration_minutes=20, is_published=True),
        instructor, db_session,
    )
    assert lesson.id is not None
    assert lesson.course_id == course.id

    lessons = await lesson_service.list_lessons(course.id, instructor, db_session)
    assert len(lessons) >= 1

    fetched = await lesson_service.get_lesson(lesson.id, db_session)
    assert fetched.id == lesson.id

    updated = await lesson_service.update_lesson(
        lesson.id,
        LessonUpdate(title="Updated Lesson", duration_minutes=40),
        instructor, db_session,
    )
    assert updated.title == "Updated Lesson"

    await lesson_service.delete_lesson(lesson.id, instructor, db_session)
    with pytest.raises(HTTPException):
        await lesson_service.get_lesson(lesson.id, db_session)


@pytest.mark.asyncio
async def test_lessons_service_add_to_nonexistent_course(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"lne_instr_{s}@test.com", username=f"lne_instr_{s}",
                   full_name="LNE Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    with pytest.raises(HTTPException) as exc_info:
        await lesson_service.add_lesson(
            999999,
            LessonCreate(title="Ghost", content="Ghost content", order_num=1, duration_minutes=10, is_published=False),
            instructor, db_session,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_enrollment_service_full_flow(db_session: AsyncSession):
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"e_instr_{s}@test.com", username=f"e_instr_{s}",
                   full_name="E Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    student = await auth_service.register(
        UserCreate(email=f"e_stu_{s}@test.com", username=f"e_stu_{s}",
                   full_name="E Student", role=UserRole.student, password="pass123"),
        db_session,
    )

    course = await course_service.create_course(
        CourseCreate(title="Enrollment Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    from app.repositories.course import CourseRepository
    course_repo = CourseRepository(db_session)
    await course_repo.publish(course)

    enrollment = await enrollment_service.enroll_student(course.id, student, db_session)
    assert enrollment.id is not None
    assert enrollment.progress == 0.0

    enrollments = await enrollment_service.get_my_enrollments(student, db_session)
    assert len(enrollments) >= 1

    enrollment = await enrollment_service.update_progress(enrollment.id, 50.0, student, db_session)
    assert enrollment.progress == 50.0

    enrollment = await enrollment_service.update_progress(enrollment.id, 100.0, student, db_session)
    assert enrollment.completed_at is not None

    from app.repositories.certificate import CertificateRepository
    cert_repo = CertificateRepository(db_session)
    certs = await cert_repo.get_by_student(student.id)
    assert len(certs) == 1
    assert certs[0].course_id == course.id


@pytest.mark.asyncio
async def test_enrollment_enroll_duplicate(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"dup_e_instr_{s}@test.com", username=f"dup_e_instr_{s}",
                   full_name="Dup E Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    student = await auth_service.register(
        UserCreate(email=f"dup_e_stu_{s}@test.com", username=f"dup_e_stu_{s}",
                   full_name="Dup E Stu", role=UserRole.student, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="Dup Enroll", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    from app.repositories.course import CourseRepository
    await CourseRepository(db_session).publish(course)

    await enrollment_service.enroll_student(course.id, student, db_session)
    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.enroll_student(course.id, student, db_session)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_quiz_service_full_flow(db_session: AsyncSession):
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"q_instr_{s}@test.com", username=f"q_instr_{s}",
                   full_name="Q Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    student = await auth_service.register(
        UserCreate(email=f"q_stu_{s}@test.com", username=f"q_stu_{s}",
                   full_name="Q Stu", role=UserRole.student, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="Quiz Svc Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    questions = [
        {"question": "2+2?", "options": ["3", "4"], "correct_answer": "4"},
        {"question": "Sky color?", "options": ["red", "blue"], "correct_answer": "blue"},
    ]
    quiz = await quiz_service.create_quiz(
        QuizCreate(course_id=course.id, title="Svc Quiz", questions=questions, passing_score=50),
        instructor, db_session,
    )
    assert quiz.id is not None

    quizzes = await quiz_service.list_quizzes(course.id, db_session)
    assert len(quizzes) >= 1

    fetched = await quiz_service.get_quiz(quiz.id, db_session)
    assert fetched.id == quiz.id

    attempt = await quiz_service.submit_attempt(quiz.id, ["4", "blue"], student, db_session)
    assert attempt.passed is True
    assert attempt.score == 100.0

    attempt2 = await quiz_service.submit_attempt(quiz.id, ["3", "red"], student, db_session)
    assert attempt2.passed is False
    assert attempt2.score == 0.0

    results = await quiz_service.get_attempt_results(quiz.id, student, db_session)
    assert len(results) >= 2

    updated = await quiz_service.update_quiz(
        quiz.id,
        QuizUpdate(title="Updated Quiz", passing_score=80),
        instructor, db_session,
    )
    assert updated.title == "Updated Quiz"

    await quiz_service.delete_quiz(quiz.id, instructor, db_session)
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        await quiz_service.get_quiz(quiz.id, db_session)


@pytest.mark.asyncio
async def test_certificate_service(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"cert_svc_instr_{s}@test.com", username=f"cert_svc_instr_{s}",
                   full_name="Cert Svc Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    student = await auth_service.register(
        UserCreate(email=f"cert_svc_stu_{s}@test.com", username=f"cert_svc_stu_{s}",
                   full_name="Cert Svc Student", role=UserRole.student, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="Cert Svc Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    from app.repositories.course import CourseRepository
    await CourseRepository(db_session).publish(course)

    enrollment = await enrollment_service.enroll_student(course.id, student, db_session)
    await enrollment_service.update_progress(enrollment.id, 100.0, student, db_session)

    certs = await cert_service.get_my_certificates(student, db_session)
    assert len(certs) == 1

    verify_result = await cert_service.verify_certificate(certs[0].certificate_number, db_session)
    assert verify_result.valid is True
    assert verify_result.student_full_name == student.full_name

    with pytest.raises(HTTPException) as exc_info:
        await cert_service.verify_certificate("CERT-NONEXISTENT", db_session)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_analytics_service(db_session: AsyncSession):
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"an_svc_instr_{s}@test.com", username=f"an_svc_instr_{s}",
                   full_name="An Svc Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    student = await auth_service.register(
        UserCreate(email=f"an_svc_stu_{s}@test.com", username=f"an_svc_stu_{s}",
                   full_name="An Svc Stu", role=UserRole.student, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="An Svc Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    from app.repositories.course import CourseRepository
    await CourseRepository(db_session).publish(course)

    enrollment = await enrollment_service.enroll_student(course.id, student, db_session)
    await enrollment_service.update_progress(enrollment.id, 75.0, student, db_session)

    top = await analytics_service.get_top_courses(db_session)
    assert isinstance(top, list)

    progress = await analytics_service.get_student_progress(student.id, db_session)
    assert progress["student_id"] == student.id
    assert progress["total_enrollments"] >= 1

    overview = await analytics_service.get_platform_overview(db_session)
    assert overview["total_users"] >= 2
    assert overview["total_courses"] >= 1


@pytest.mark.asyncio
async def test_enrollment_get_course_students_not_found(db_session: AsyncSession, test_admin):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.get_course_students(999999, test_admin, db_session)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_enrollment_update_progress_not_found(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    student = await auth_service.register(
        UserCreate(email=f"prog_nf_{s}@test.com", username=f"prog_nf_{s}",
                   full_name="Prog NF", role=UserRole.student, password="pass123"),
        db_session,
    )
    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.update_progress(999999, 50.0, student, db_session)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_lesson_service_student_sees_only_published(db_session: AsyncSession):
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"ls_instr_{s}@test.com", username=f"ls_instr_{s}",
                   full_name="LS Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    student = await auth_service.register(
        UserCreate(email=f"ls_stu_{s}@test.com", username=f"ls_stu_{s}",
                   full_name="LS Stu", role=UserRole.student, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="LS Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    await lesson_service.add_lesson(
        course.id,
        LessonCreate(title="Published", content="...", order_num=1, duration_minutes=10, is_published=True),
        instructor, db_session,
    )
    await lesson_service.add_lesson(
        course.id,
        LessonCreate(title="Hidden", content="...", order_num=2, duration_minutes=5, is_published=False),
        instructor, db_session,
    )

    student_lessons = await lesson_service.list_lessons(course.id, student, db_session)
    titles = [l.title for l in student_lessons]
    assert "Published" in titles
    assert "Hidden" not in titles

    instructor_lessons = await lesson_service.list_lessons(course.id, instructor, db_session)
    instr_titles = [l.title for l in instructor_lessons]
    assert "Published" in instr_titles
    assert "Hidden" in instr_titles


@pytest.mark.asyncio
async def test_quiz_service_nonexistent_course(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"qnc_instr_{s}@test.com", username=f"qnc_instr_{s}",
                   full_name="QNC Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    with pytest.raises(HTTPException) as exc_info:
        await quiz_service.create_quiz(
            QuizCreate(course_id=999999, title="Ghost Quiz", questions=[], passing_score=70),
            instructor, db_session,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_courses_service_delete_forbidden(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"delf_instr_{s}@test.com", username=f"delf_instr_{s}",
                   full_name="DelF Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    other = await auth_service.register(
        UserCreate(email=f"delf_other_{s}@test.com", username=f"delf_other_{s}",
                   full_name="DelF Other", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="Delf Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    with pytest.raises(HTTPException) as exc_info:
        await course_service.delete_course(course.id, other, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_courses_service_publish_forbidden(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await auth_service.register(
        UserCreate(email=f"pubf_instr_{s}@test.com", username=f"pubf_instr_{s}",
                   full_name="PubF Instr", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    other = await auth_service.register(
        UserCreate(email=f"pubf_other_{s}@test.com", username=f"pubf_other_{s}",
                   full_name="PubF Other", role=UserRole.instructor, password="pass123"),
        db_session,
    )
    course = await course_service.create_course(
        CourseCreate(title="PubF Course", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    with pytest.raises(HTTPException) as exc_info:
        await course_service.publish_course(course.id, other, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_password_utilities():
    password = "my_test_password"
    hashed = auth_service.get_password_hash(password)
    assert auth_service.verify_password(password, hashed) is True
    assert auth_service.verify_password("wrong_password", hashed) is False


@pytest.mark.asyncio
async def test_create_access_token():
    token = auth_service.create_access_token({"sub": "123"})
    assert isinstance(token, str)
    assert len(token) > 0
