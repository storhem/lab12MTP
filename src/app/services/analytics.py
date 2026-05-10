from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate import Certificate
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.quiz import QuizAttempt
from app.models.user import User


async def get_top_courses(session: AsyncSession, limit: int = 10) -> list[dict]:
    result = await session.execute(
        select(
            Course.id,
            Course.title,
            Course.level,
            Course.price,
            func.count(Enrollment.id).label("enrollment_count"),
            func.avg(Enrollment.progress).label("avg_progress"),
        )
        .join(Enrollment, Enrollment.course_id == Course.id, isouter=True)
        .where(Course.is_published == True)
        .group_by(Course.id, Course.title, Course.level, Course.price)
        .order_by(func.count(Enrollment.id).desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "course_id": row.id,
            "title": row.title,
            "level": row.level,
            "price": row.price,
            "enrollment_count": row.enrollment_count or 0,
            "avg_progress": round(float(row.avg_progress or 0), 2),
        }
        for row in rows
    ]


async def get_student_progress(student_id: int, session: AsyncSession) -> dict:
    enrollments_result = await session.execute(
        select(Enrollment).where(Enrollment.student_id == student_id, Enrollment.is_active == True)
    )
    enrollments = list(enrollments_result.scalars().all())

    completed = [e for e in enrollments if e.completed_at is not None]
    in_progress = [e for e in enrollments if e.completed_at is None]

    attempts_result = await session.execute(
        select(QuizAttempt).where(QuizAttempt.student_id == student_id)
    )
    attempts = list(attempts_result.scalars().all())

    certs_result = await session.execute(
        select(Certificate).where(Certificate.student_id == student_id)
    )
    certificates = list(certs_result.scalars().all())

    avg_progress = (
        sum(e.progress for e in enrollments) / len(enrollments) if enrollments else 0.0
    )

    return {
        "student_id": student_id,
        "total_enrollments": len(enrollments),
        "completed_courses": len(completed),
        "in_progress_courses": len(in_progress),
        "avg_progress": round(avg_progress, 2),
        "total_quiz_attempts": len(attempts),
        "passed_quizzes": sum(1 for a in attempts if a.passed),
        "certificates_earned": len(certificates),
    }


async def get_platform_overview(session: AsyncSession) -> dict:
    total_users_result = await session.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar_one()

    total_courses_result = await session.execute(select(func.count(Course.id)))
    total_courses = total_courses_result.scalar_one()

    published_courses_result = await session.execute(
        select(func.count(Course.id)).where(Course.is_published == True)
    )
    published_courses = published_courses_result.scalar_one()

    total_enrollments_result = await session.execute(select(func.count(Enrollment.id)))
    total_enrollments = total_enrollments_result.scalar_one()

    total_certs_result = await session.execute(select(func.count(Certificate.id)))
    total_certificates = total_certs_result.scalar_one()

    total_attempts_result = await session.execute(select(func.count(QuizAttempt.id)))
    total_attempts = total_attempts_result.scalar_one()

    passed_attempts_result = await session.execute(
        select(func.count(QuizAttempt.id)).where(QuizAttempt.passed == True)
    )
    passed_attempts = passed_attempts_result.scalar_one()

    return {
        "total_users": total_users,
        "total_courses": total_courses,
        "published_courses": published_courses,
        "total_enrollments": total_enrollments,
        "total_certificates_issued": total_certificates,
        "total_quiz_attempts": total_attempts,
        "passed_quiz_attempts": passed_attempts,
        "quiz_pass_rate": round((passed_attempts / total_attempts * 100) if total_attempts else 0.0, 2),
    }
