from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate import Certificate
from app.models.user import User
from app.repositories.certificate import CertificateRepository
from app.schemas.certificate import CertificateVerifyResponse


async def get_my_certificates(student: User, session: AsyncSession) -> list[Certificate]:
    repo = CertificateRepository(session)
    return await repo.get_by_student(student.id)


async def verify_certificate(certificate_number: str, session: AsyncSession) -> CertificateVerifyResponse:
    repo = CertificateRepository(session)
    certificate = await repo.get_by_number(certificate_number)
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
    return CertificateVerifyResponse(
        valid=True,
        certificate_number=certificate.certificate_number,
        student_full_name=certificate.student.full_name,
        course_title=certificate.course.title,
        issued_at=certificate.issued_at,
    )
