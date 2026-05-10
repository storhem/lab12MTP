from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.certificate import CertificateResponse, CertificateVerifyResponse
from app.services import auth as auth_service
from app.services import certificates as cert_service

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("/my", response_model=list[CertificateResponse])
async def get_my_certificates(
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CertificateResponse]:
    return await cert_service.get_my_certificates(current_user, session)


@router.get("/{certificate_number}/verify", response_model=CertificateVerifyResponse)
async def verify_certificate(
    certificate_number: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CertificateVerifyResponse:
    return await cert_service.verify_certificate(certificate_number, session)
