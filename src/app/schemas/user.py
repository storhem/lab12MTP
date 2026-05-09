from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.student


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserInDB(UserResponse):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
