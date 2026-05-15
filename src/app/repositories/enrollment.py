from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Enrollment, session)

    async def get_by_student(self, student_id: int, skip: int = 0, limit: int = 100) -> list[Enrollment]:
        result = await self.session.execute(
            select(Enrollment)
            .where(Enrollment.student_id == student_id, Enrollment.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_course(self, course_id: int, skip: int = 0, limit: int = 100) -> list[Enrollment]:
        result = await self.session.execute(
            select(Enrollment)
            .where(Enrollment.course_id == course_id, Enrollment.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_student_and_course(self, student_id: int, course_id: int) -> Enrollment | None:
        result = await self.session.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_progress(self, enrollment: Enrollment, progress: float) -> Enrollment:
        enrollment.progress = progress
        if progress >= 100.0:
            enrollment.completed_at = datetime.now(timezone.utc)
        self.session.add(enrollment)
        await self.session.commit()
        await self.session.refresh(enrollment)
        return enrollment
