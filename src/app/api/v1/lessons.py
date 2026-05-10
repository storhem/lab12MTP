from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User, UserRole
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.services import auth as auth_service
from app.services import lessons as lesson_service

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/course/{course_id}", response_model=LessonResponse, status_code=201)
async def add_lesson(
    course_id: int,
    lesson_data: LessonCreate,
    current_user: Annotated[
        User,
        Depends(auth_service.require_roles(UserRole.instructor, UserRole.admin)),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LessonResponse:
    return await lesson_service.add_lesson(course_id, lesson_data, current_user, session)


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LessonResponse:
    return await lesson_service.get_lesson(lesson_id, session)


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LessonResponse:
    return await lesson_service.update_lesson(lesson_id, lesson_data, current_user, session)


@router.delete("/{lesson_id}", status_code=204)
async def delete_lesson(
    lesson_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    await lesson_service.delete_lesson(lesson_id, current_user, session)
