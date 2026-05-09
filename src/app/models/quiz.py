from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.lesson import Lesson
    from app.models.user import User


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    questions: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    course: Mapped["Course"] = relationship("Course", back_populates="quizzes", lazy="selectin")
    lesson: Mapped["Lesson | None"] = relationship("Lesson", back_populates="quizzes", lazy="selectin")
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt", back_populates="quiz", lazy="selectin", cascade="all, delete-orphan"
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="attempts", lazy="selectin")
    student: Mapped["User"] = relationship("User", back_populates="quiz_attempts", lazy="selectin")
