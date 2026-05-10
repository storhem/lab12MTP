from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Course, session)

    async def get_published(self, skip: int = 0, limit: int = 100) -> list[Course]:
        result = await self.session.execute(
            select(Course).where(Course.is_published == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_instructor(self, instructor_id: int, skip: int = 0, limit: int = 100) -> list[Course]:
        result = await self.session.execute(
            select(Course).where(Course.instructor_id == instructor_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def publish(self, course: Course) -> Course:
        course.is_published = True
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)
        return course

    async def unpublish(self, course: Course) -> Course:
        course.is_published = False
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)
        return course
