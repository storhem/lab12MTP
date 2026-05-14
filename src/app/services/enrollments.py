import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate import Certificate
from app.models.enrollment import Enrollment
from app.models.user import User
from app.repositories.certificate import CertificateRepository
from app.repositories.course import CourseRepository
from app.repositories.enrollment import EnrollmentRepository


async def enroll_student(course_id: int, student: User, session: AsyncSession) -> Enrollment:
    course_repo = CourseRepository(session)
    course = await course_repo.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    if not course.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enroll in an unpublished course",
        )
    enrollment_repo = EnrollmentRepository(session)
    existing = await enrollment_repo.get_by_student_and_course(student.id, course_id)
    if existing:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already enrolled in this course",
            )
        existing.is_active = True
        existing.progress = 0.0
        existing.completed_at = None
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing
    enrollment = await enrollment_repo.create(
        student_id=student.id,
        course_id=course_id,
    )
    return enrollment


async def get_my_enrollments(student: User, session: AsyncSession) -> list[Enrollment]:
    repo = EnrollmentRepository(session)
    return await repo.get_by_student(student.id)


async def get_enrollment(enrollment_id: int, student: User, session: AsyncSession) -> Enrollment:
    repo = EnrollmentRepository(session)
    enrollment = await repo.get(enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )
    if enrollment.student_id != student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this enrollment",
        )
    return enrollment


async def update_progress(
    enrollment_id: int, progress: float, student: User, session: AsyncSession
) -> Enrollment:
    enrollment = await get_enrollment(enrollment_id, student, session)
    if not enrollment.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enrollment is not active",
        )
    repo = EnrollmentRepository(session)
    enrollment = await repo.update_progress(enrollment, progress)
    if progress >= 100.0:
        await issue_certificate(enrollment, session)
    return enrollment


async def issue_certificate(enrollment: Enrollment, session: AsyncSession) -> Certificate:
    cert_repo = CertificateRepository(session)
    existing_cert = await cert_repo.get_by_enrollment(enrollment.id)
    if existing_cert:
        return existing_cert
    certificate_number = f"CERT-{uuid.uuid4().hex.upper()[:12]}"
    certificate = await cert_repo.create(
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        enrollment_id=enrollment.id,
        certificate_number=certificate_number,
    )
    return certificate


async def get_course_students(course_id: int, current_user: User, session: AsyncSession) -> list[Enrollment]:
    from app.models.user import UserRole
    course_repo = CourseRepository(session)
    course = await course_repo.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view students of this course",
        )
    enrollment_repo = EnrollmentRepository(session)
    return await enrollment_repo.get_by_course(course_id)
