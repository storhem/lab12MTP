from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    user = await auth_service.register(user_data, session)
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    token = await auth_service.login(credentials.email, credentials.password, session)
    return Token(access_token=token)


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    token = await auth_service.login(form_data.username, form_data.password, session)
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(auth_service.get_current_active_user)],
) -> UserResponse:
    return current_user
