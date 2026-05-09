import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lesson import Lesson
    from app.models.enrollment import Enrollment
    from app.models.quiz import Quiz
    from app.models.certificate import Certificate


class CourseLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    level: Mapped[CourseLevel] = mapped_column(
        Enum(CourseLevel, name="courselevel"), default=CourseLevel.beginner, nullable=False
    )
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    instructor: Mapped["User"] = relationship("User", back_populates="courses", lazy="selectin")
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
    certificates: Mapped[list["Certificate"]] = relationship(
        "Certificate", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
