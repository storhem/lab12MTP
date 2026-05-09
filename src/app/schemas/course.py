from datetime import datetime

from pydantic import BaseModel, Field

from app.models.course import CourseLevel
from app.schemas.user import UserResponse


class CourseBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    level: CourseLevel = CourseLevel.beginner
    price: float = Field(default=0.0, ge=0.0)
    tags: str = Field(default="", max_length=500)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    level: CourseLevel | None = None
    price: float | None = Field(default=None, ge=0.0)
    tags: str | None = Field(default=None, max_length=500)
    is_published: bool | None = None


class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseDetailResponse(CourseResponse):
    instructor: UserResponse

    model_config = {"from_attributes": True}
