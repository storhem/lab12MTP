from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course
    from app.models.enrollment import Enrollment


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.id"), nullable=False, unique=True)
    certificate_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    student: Mapped["User"] = relationship("User", back_populates="certificates", lazy="selectin")
    course: Mapped["Course"] = relationship("Course", back_populates="certificates", lazy="selectin")
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment", back_populates="certificate", lazy="selectin"
    )
