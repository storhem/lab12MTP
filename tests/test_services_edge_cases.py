import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.schemas.course import CourseCreate
from app.services import auth as auth_service
from app.services import courses as course_service
from app.services import enrollments as enrollment_service
from app.services import quizzes as quiz_service
from app.services import lessons as lesson_service
from app.schemas.quiz import QuizCreate
from app.schemas.lesson import LessonCreate, LessonUpdate
from app.repositories.course import CourseRepository
from app.repositories.enrollment import EnrollmentRepository


def uid() -> str:
    return uuid.uuid4().hex[:8]


async def make_instructor(db_session: AsyncSession, s: str):
    return await auth_service.register(
        UserCreate(email=f"ec_instr_{s}@test.com", username=f"ec_instr_{s}",
                   full_name="EC Instructor", role=UserRole.instructor, password="pass123"),
        db_session,
    )


async def make_student(db_session: AsyncSession, s: str):
    return await auth_service.register(
        UserCreate(email=f"ec_stu_{s}@test.com", username=f"ec_stu_{s}",
                   full_name="EC Student", role=UserRole.student, password="pass123"),
        db_session,
    )


async def make_published_course(instructor, db_session: AsyncSession, s: str):
    course = await course_service.create_course(
        CourseCreate(title=f"EC Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    await CourseRepository(db_session).publish(course)
    return course


@pytest.mark.asyncio
async def test_reenroll_inactive_enrollment(db_session: AsyncSession):
    s = uid()
    instructor = await make_instructor(db_session, s)
    student = await make_student(db_session, s)
    course = await make_published_course(instructor, db_session, s)

    enrollment = await enrollment_service.enroll_student(course.id, student, db_session)
    assert enrollment.is_active is True

    enrollment.is_active = False
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    assert enrollment.is_active is False

    re_enrollment = await enrollment_service.enroll_student(course.id, student, db_session)
    assert re_enrollment.is_active is True
    assert re_enrollment.progress == 0.0
    assert re_enrollment.completed_at is None


@pytest.mark.asyncio
async def test_quiz_service_update_forbidden(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await make_instructor(db_session, s)
    s2 = uid()
    other_instr = await auth_service.register(
        UserCreate(email=f"other_qi_{s2}@test.com", username=f"other_qi_{s2}",
                   full_name="Other QI", role=UserRole.instructor, password="pass123"),
        db_session,
    )

    course = await course_service.create_course(
        CourseCreate(title=f"Quiz Perm Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    quiz = await quiz_service.create_quiz(
        QuizCreate(course_id=course.id, title="Perm Quiz", questions=[], passing_score=70),
        instructor, db_session,
    )

    from app.schemas.quiz import QuizUpdate
    with pytest.raises(HTTPException) as exc_info:
        await quiz_service.update_quiz(quiz.id, QuizUpdate(title="Hacked"), other_instr, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_quiz_service_delete_forbidden(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await make_instructor(db_session, s)
    s2 = uid()
    other_instr = await auth_service.register(
        UserCreate(email=f"del_qi_{s2}@test.com", username=f"del_qi_{s2}",
                   full_name="Del QI", role=UserRole.instructor, password="pass123"),
        db_session,
    )

    course = await course_service.create_course(
        CourseCreate(title=f"Del Quiz Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    quiz = await quiz_service.create_quiz(
        QuizCreate(course_id=course.id, title="Del Quiz", questions=[], passing_score=70),
        instructor, db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        await quiz_service.delete_quiz(quiz.id, other_instr, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_quiz_service_create_forbidden_for_other_instructor(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await make_instructor(db_session, s)
    s2 = uid()
    other_instr = await auth_service.register(
        UserCreate(email=f"cquiz_other_{s2}@test.com", username=f"cquiz_other_{s2}",
                   full_name="CQuiz Other", role=UserRole.instructor, password="pass123"),
        db_session,
    )

    course = await course_service.create_course(
        CourseCreate(title=f"Other Quiz Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        await quiz_service.create_quiz(
            QuizCreate(course_id=course.id, title="Forbidden Quiz", questions=[], passing_score=70),
            other_instr, db_session,
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_lesson_service_update_forbidden(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await make_instructor(db_session, s)
    s2 = uid()
    other_instr = await auth_service.register(
        UserCreate(email=f"lupd_other_{s2}@test.com", username=f"lupd_other_{s2}",
                   full_name="LUpd Other", role=UserRole.instructor, password="pass123"),
        db_session,
    )

    course = await course_service.create_course(
        CourseCreate(title=f"Lesson Upd Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    lesson = await lesson_service.add_lesson(
        course.id,
        LessonCreate(title="My Lesson", content="Content", order_num=1, duration_minutes=10, is_published=True),
        instructor, db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        await lesson_service.update_lesson(
            lesson.id, LessonUpdate(title="Hacked"), other_instr, db_session
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_lesson_service_delete_forbidden(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await make_instructor(db_session, s)
    s2 = uid()
    other_instr = await auth_service.register(
        UserCreate(email=f"ldel_other_{s2}@test.com", username=f"ldel_other_{s2}",
                   full_name="LDel Other", role=UserRole.instructor, password="pass123"),
        db_session,
    )

    course = await course_service.create_course(
        CourseCreate(title=f"Lesson Del Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    lesson = await lesson_service.add_lesson(
        course.id,
        LessonCreate(title="Del Lesson", content="Content", order_num=1, duration_minutes=10, is_published=True),
        instructor, db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        await lesson_service.delete_lesson(lesson.id, other_instr, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_repository_get_multi_with_filters(db_session: AsyncSession):
    from app.repositories.user import UserRepository
    s = uid()
    await auth_service.register(
        UserCreate(email=f"filt1_{s}@test.com", username=f"filt1_{s}",
                   full_name="Filt1", role=UserRole.student, password="pass123"),
        db_session,
    )
    repo = UserRepository(db_session)
    users = await repo.get_multi(skip=0, limit=10, role=UserRole.student)
    assert isinstance(users, list)
    assert len(users) >= 1


@pytest.mark.asyncio
async def test_repository_count(db_session: AsyncSession):
    from app.repositories.user import UserRepository
    repo = UserRepository(db_session)
    count = await repo.count()
    assert isinstance(count, int)
    assert count >= 0


@pytest.mark.asyncio
async def test_user_repository_get_active_users(db_session: AsyncSession):
    from app.repositories.user import UserRepository
    s = uid()
    await auth_service.register(
        UserCreate(email=f"active_{s}@test.com", username=f"active_{s}",
                   full_name="Active User", role=UserRole.student, password="pass123"),
        db_session,
    )
    repo = UserRepository(db_session)
    active = await repo.get_active_users()
    assert isinstance(active, list)
    assert all(u.is_active for u in active)


@pytest.mark.asyncio
async def test_course_repository_list_by_instructor(db_session: AsyncSession):
    s = uid()
    instructor = await make_instructor(db_session, s)
    await course_service.create_course(
        CourseCreate(title=f"Repo Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )
    repo = CourseRepository(db_session)
    courses = await repo.get_by_instructor(instructor.id)
    assert len(courses) >= 1
    assert all(c.instructor_id == instructor.id for c in courses)


@pytest.mark.asyncio
async def test_quiz_attempt_repository_get_by_student(db_session: AsyncSession):
    from app.repositories.quiz import QuizAttemptRepository
    s = uid()
    instructor = await make_instructor(db_session, s)
    student = await make_student(db_session, s)
    course = await course_service.create_course(
        CourseCreate(title=f"QA Repo Course {s}", description="Desc", level="beginner", price=0.0, tags=""),
        instructor, db_session,
    )

    quiz = await quiz_service.create_quiz(
        QuizCreate(course_id=course.id, title="QA Repo Quiz",
                   questions=[{"question": "Q?", "options": ["a", "b"], "correct_answer": "a"}],
                   passing_score=50),
        instructor, db_session,
    )

    await quiz_service.submit_attempt(quiz.id, ["a"], student, db_session)
    await quiz_service.submit_attempt(quiz.id, ["b"], student, db_session)

    repo = QuizAttemptRepository(db_session)
    attempts = await repo.get_by_student(student.id)
    assert len(attempts) >= 2


@pytest.mark.asyncio
async def test_enrollment_update_progress_inactive_fails(db_session: AsyncSession):
    from fastapi import HTTPException
    s = uid()
    instructor = await make_instructor(db_session, s)
    student = await make_student(db_session, s)
    course = await make_published_course(instructor, db_session, s)

    enrollment = await enrollment_service.enroll_student(course.id, student, db_session)

    enrollment.is_active = False
    db_session.add(enrollment)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.update_progress(enrollment.id, 50.0, student, db_session)
    assert exc_info.value.status_code == 400
