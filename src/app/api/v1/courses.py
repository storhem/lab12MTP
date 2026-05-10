from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User, UserRole
from app.schemas.course import CourseCreate, CourseDetailResponse, CourseResponse, CourseUpdate
from app.schemas.enrollment import EnrollmentResponse
from app.schemas.lesson import LessonResponse
from app.services import auth as auth_service
from app.services import courses as course_service
from app.services import enrollments as enrollment_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    course_data: CourseCreate,
    current_user: Annotated[
        User,
        Depends(auth_service.require_roles(UserRole.instructor, UserRole.admin)),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CourseResponse:
    return await course_service.create_course(course_data, current_user, session)


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    instructor_id: int | None = Query(default=None),
) -> list[CourseResponse]:
    return await course_service.list_courses(
        skip=skip,
        limit=limit,
        published_only=True,
        instructor_id=instructor_id,
        session=session,
    )


@router.get("/all", response_model=list[CourseResponse])
async def list_all_courses(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    instructor_id: int | None = Query(default=None),
) -> list[CourseResponse]:
    published_only = current_user.role not in (UserRole.admin, UserRole.instructor)
    return await course_service.list_courses(
        skip=skip,
        limit=limit,
        published_only=published_only,
        instructor_id=instructor_id,
        session=session,
    )


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CourseDetailResponse:
    return await course_service.get_course(course_id, session)


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CourseResponse:
    return await course_service.update_course(course_id, course_data, current_user, session)


@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    await course_service.delete_course(course_id, current_user, session)


@router.post("/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CourseResponse:
    return await course_service.publish_course(course_id, current_user, session)


@router.post("/{course_id}/unpublish", response_model=CourseResponse)
async def unpublish_course(
    course_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CourseResponse:
    return await course_service.unpublish_course(course_id, current_user, session)


@router.get("/{course_id}/students", response_model=list[EnrollmentResponse])
async def get_course_students(
    course_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[EnrollmentResponse]:
    return await enrollment_service.get_course_students(course_id, session)


@router.get("/{course_id}/lessons", response_model=list[LessonResponse])
async def get_course_lessons(
    course_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[LessonResponse]:
    from app.services import lessons as lesson_service
    return await lesson_service.list_lessons(course_id, current_user, session, skip=skip, limit=limit)
