from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.repositories.base import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Lesson, session)

    async def get_by_course(self, course_id: int, skip: int = 0, limit: int = 100) -> list[Lesson]:
        result = await self.session.execute(
            select(Lesson)
            .where(Lesson.course_id == course_id)
            .order_by(Lesson.order_num)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_published_by_course(self, course_id: int) -> list[Lesson]:
        result = await self.session.execute(
            select(Lesson)
            .where(Lesson.course_id == course_id, Lesson.is_published == True)
            .order_by(Lesson.order_num)
        )
        return list(result.scalars().all())

    async def get_max_order_num(self, course_id: int) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.max(Lesson.order_num)).where(Lesson.course_id == course_id)
        )
        val = result.scalar_one_or_none()
        return val if val is not None else 0
