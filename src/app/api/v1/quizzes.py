from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User, UserRole
from app.schemas.quiz import QuizAttemptCreate, QuizAttemptResponse, QuizCreate, QuizResponse, QuizUpdate
from app.services import auth as auth_service
from app.services import quizzes as quiz_service

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("", response_model=QuizResponse, status_code=201)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: Annotated[
        User,
        Depends(auth_service.require_roles(UserRole.instructor, UserRole.admin)),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizResponse:
    return await quiz_service.create_quiz(quiz_data, current_user, session)


@router.get("/course/{course_id}", response_model=list[QuizResponse])
async def list_quizzes(
    course_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[QuizResponse]:
    return await quiz_service.list_quizzes(course_id, session, skip=skip, limit=limit)


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizResponse:
    return await quiz_service.get_quiz(quiz_id, session)


@router.put("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: int,
    quiz_data: QuizUpdate,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizResponse:
    return await quiz_service.update_quiz(quiz_id, quiz_data, current_user, session)


@router.delete("/{quiz_id}", status_code=204)
async def delete_quiz(
    quiz_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    await quiz_service.delete_quiz(quiz_id, current_user, session)


@router.post("/{quiz_id}/attempt", response_model=QuizAttemptResponse, status_code=201)
async def submit_attempt(
    quiz_id: int,
    attempt_data: QuizAttemptCreate,
    current_user: Annotated[
        User,
        Depends(auth_service.require_roles(UserRole.student)),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizAttemptResponse:
    return await quiz_service.submit_attempt(quiz_id, attempt_data.answers, current_user, session)


@router.get("/{quiz_id}/results", response_model=list[QuizAttemptResponse])
async def get_results(
    quiz_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[QuizAttemptResponse]:
    return await quiz_service.get_attempt_results(quiz_id, current_user, session)
