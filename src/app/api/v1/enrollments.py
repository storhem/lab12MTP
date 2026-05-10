from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User, UserRole
from app.schemas.enrollment import EnrollmentCreate, EnrollmentResponse, ProgressUpdate
from app.services import auth as auth_service
from app.services import enrollments as enrollment_service

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentResponse, status_code=201)
async def enroll(
    enrollment_data: EnrollmentCreate,
    current_user: Annotated[
        User,
        Depends(auth_service.require_roles(UserRole.student)),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EnrollmentResponse:
    return await enrollment_service.enroll_student(enrollment_data.course_id, current_user, session)


@router.get("/my", response_model=list[EnrollmentResponse])
async def get_my_enrollments(
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[EnrollmentResponse]:
    return await enrollment_service.get_my_enrollments(current_user, session)


@router.put("/{enrollment_id}/progress", response_model=EnrollmentResponse)
async def update_progress(
    enrollment_id: int,
    progress_data: ProgressUpdate,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EnrollmentResponse:
    return await enrollment_service.update_progress(
        enrollment_id, progress_data.progress, current_user, session
    )
