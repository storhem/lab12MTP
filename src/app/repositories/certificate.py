from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate import Certificate
from app.repositories.base import BaseRepository


class CertificateRepository(BaseRepository[Certificate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Certificate, session)

    async def get_by_student(self, student_id: int) -> list[Certificate]:
        result = await self.session.execute(
            select(Certificate).where(Certificate.student_id == student_id)
        )
        return list(result.scalars().all())

    async def get_by_number(self, certificate_number: str) -> Certificate | None:
        result = await self.session.execute(
            select(Certificate).where(Certificate.certificate_number == certificate_number)
        )
        return result.scalar_one_or_none()

    async def get_by_enrollment(self, enrollment_id: int) -> Certificate | None:
        result = await self.session.execute(
            select(Certificate).where(Certificate.enrollment_id == enrollment_id)
        )
        return result.scalar_one_or_none()
