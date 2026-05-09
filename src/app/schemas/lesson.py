from datetime import datetime

from pydantic import BaseModel, Field


class LessonBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    order_num: int = Field(default=1, ge=1)
    duration_minutes: int = Field(default=0, ge=0)
    is_published: bool = False


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    order_num: int | None = Field(default=None, ge=1)
    duration_minutes: int | None = Field(default=None, ge=0)
    is_published: bool | None = None


class LessonResponse(LessonBase):
    id: int
    course_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
