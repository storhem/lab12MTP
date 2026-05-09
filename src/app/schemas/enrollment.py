from datetime import datetime

from pydantic import BaseModel, Field


class EnrollmentBase(BaseModel):
    course_id: int


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    progress: float | None = Field(default=None, ge=0.0, le=100.0)
    is_active: bool | None = None


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrolled_at: datetime
    completed_at: datetime | None
    progress: float
    is_active: bool

    model_config = {"from_attributes": True}


class ProgressUpdate(BaseModel):
    progress: float = Field(ge=0.0, le=100.0)
