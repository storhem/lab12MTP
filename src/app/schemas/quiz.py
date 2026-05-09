from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QuizBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    questions: list[Any] = Field(default_factory=list)
    passing_score: int = Field(default=70, ge=0, le=100)


class QuizCreate(QuizBase):
    course_id: int
    lesson_id: int | None = None


class QuizUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    questions: list[Any] | None = None
    passing_score: int | None = Field(default=None, ge=0, le=100)
    lesson_id: int | None = None


class QuizResponse(QuizBase):
    id: int
    course_id: int
    lesson_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizAttemptCreate(BaseModel):
    answers: list[Any] = Field(default_factory=list)


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    score: float
    passed: bool
    attempted_at: datetime

    model_config = {"from_attributes": True}
