from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz, QuizAttempt
from app.repositories.base import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Quiz, session)

    async def get_by_course(self, course_id: int, skip: int = 0, limit: int = 100) -> list[Quiz]:
        result = await self.session.execute(
            select(Quiz).where(Quiz.course_id == course_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_lesson(self, lesson_id: int) -> list[Quiz]:
        result = await self.session.execute(
            select(Quiz).where(Quiz.lesson_id == lesson_id)
        )
        return list(result.scalars().all())


class QuizAttemptRepository(BaseRepository[QuizAttempt]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(QuizAttempt, session)

    async def get_by_quiz_and_student(self, quiz_id: int, student_id: int) -> list[QuizAttempt]:
        result = await self.session.execute(
            select(QuizAttempt)
            .where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.student_id == student_id)
            .order_by(QuizAttempt.attempted_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_student(self, student_id: int, skip: int = 0, limit: int = 100) -> list[QuizAttempt]:
        result = await self.session.execute(
            select(QuizAttempt)
            .where(QuizAttempt.student_id == student_id)
            .order_by(QuizAttempt.attempted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
