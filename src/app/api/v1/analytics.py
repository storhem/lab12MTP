from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User, UserRole
from app.services import analytics as analytics_service
from app.services import auth as auth_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-courses")
async def get_top_courses(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    return await analytics_service.get_top_courses(session, limit=limit)


@router.get("/student/{student_id}/progress")
async def get_student_progress(
    student_id: int,
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    if current_user.role != UserRole.admin and current_user.id != student_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this student's progress",
        )
    return await analytics_service.get_student_progress(student_id, session)


@router.get("/overview")
async def get_platform_overview(
    current_user: Annotated[
        User,
        Depends(auth_service.require_roles(UserRole.admin)),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    return await analytics_service.get_platform_overview(session)
