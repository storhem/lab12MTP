from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.user import User, UserRole
from app.repositories.course import CourseRepository
from app.schemas.course import CourseCreate, CourseUpdate


async def create_course(course_data: CourseCreate, instructor: User, session: AsyncSession) -> Course:
    repo = CourseRepository(session)
    course = await repo.create(
        title=course_data.title,
        description=course_data.description,
        instructor_id=instructor.id,
        level=course_data.level,
        price=course_data.price,
        tags=course_data.tags,
    )
    return course


async def list_courses(
    skip: int = 0,
    limit: int = 100,
    published_only: bool = True,
    instructor_id: int | None = None,
    session: AsyncSession = None,
) -> list[Course]:
    repo = CourseRepository(session)
    if instructor_id is not None:
        courses = await repo.get_by_instructor(instructor_id, skip=skip, limit=limit)
        if published_only:
            courses = [c for c in courses if c.is_published]
        return courses
    if published_only:
        return await repo.get_published(skip=skip, limit=limit)
    return await repo.get_multi(skip=skip, limit=limit)


async def get_course(course_id: int, session: AsyncSession) -> Course:
    repo = CourseRepository(session)
    course = await repo.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return course


async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User,
    session: AsyncSession,
) -> Course:
    course = await get_course(course_id, session)
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this course",
        )
    repo = CourseRepository(session)
    update_data = course_data.model_dump(exclude_unset=True)
    return await repo.update(course, **update_data)


async def delete_course(course_id: int, current_user: User, session: AsyncSession) -> None:
    course = await get_course(course_id, session)
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this course",
        )
    repo = CourseRepository(session)
    await repo.delete(course)


async def publish_course(course_id: int, current_user: User, session: AsyncSession) -> Course:
    course = await get_course(course_id, session)
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to publish this course",
        )
    repo = CourseRepository(session)
    return await repo.publish(course)


async def unpublish_course(course_id: int, current_user: User, session: AsyncSession) -> Course:
    course = await get_course(course_id, session)
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to unpublish this course",
        )
    repo = CourseRepository(session)
    return await repo.unpublish(course)
