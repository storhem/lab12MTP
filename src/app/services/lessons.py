from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.user import User, UserRole
from app.repositories.course import CourseRepository
from app.repositories.lesson import LessonRepository
from app.schemas.lesson import LessonCreate, LessonUpdate


async def get_lesson_or_404(lesson_id: int, session: AsyncSession) -> Lesson:
    repo = LessonRepository(session)
    lesson = await repo.get(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return lesson


async def check_course_ownership(course_id: int, current_user: User, session: AsyncSession) -> None:
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
            detail="Not authorized to manage lessons for this course",
        )


async def add_lesson(
    course_id: int,
    lesson_data: LessonCreate,
    current_user: User,
    session: AsyncSession,
) -> Lesson:
    await check_course_ownership(course_id, current_user, session)
    lesson_repo = LessonRepository(session)
    max_order = await lesson_repo.get_max_order_num(course_id)
    order_num = lesson_data.order_num if lesson_data.order_num > max_order else max_order + 1
    lesson = await lesson_repo.create(
        course_id=course_id,
        title=lesson_data.title,
        content=lesson_data.content,
        order_num=order_num,
        duration_minutes=lesson_data.duration_minutes,
        is_published=lesson_data.is_published,
    )
    return lesson


async def list_lessons(
    course_id: int,
    current_user: User,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[Lesson]:
    course_repo = CourseRepository(session)
    course = await course_repo.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    lesson_repo = LessonRepository(session)
    if current_user.role == UserRole.student:
        return await lesson_repo.get_published_by_course(course_id)
    return await lesson_repo.get_by_course(course_id, skip=skip, limit=limit)


async def get_lesson(lesson_id: int, session: AsyncSession) -> Lesson:
    return await get_lesson_or_404(lesson_id, session)


async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    current_user: User,
    session: AsyncSession,
) -> Lesson:
    lesson = await get_lesson_or_404(lesson_id, session)
    await check_course_ownership(lesson.course_id, current_user, session)
    lesson_repo = LessonRepository(session)
    update_data = lesson_data.model_dump(exclude_unset=True)
    return await lesson_repo.update(lesson, **update_data)


async def delete_lesson(lesson_id: int, current_user: User, session: AsyncSession) -> None:
    lesson = await get_lesson_or_404(lesson_id, session)
    await check_course_ownership(lesson.course_id, current_user, session)
    lesson_repo = LessonRepository(session)
    await lesson_repo.delete(lesson)
