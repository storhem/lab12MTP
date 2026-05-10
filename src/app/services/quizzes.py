from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz, QuizAttempt
from app.models.user import User, UserRole
from app.repositories.course import CourseRepository
from app.repositories.quiz import QuizAttemptRepository, QuizRepository
from app.schemas.quiz import QuizCreate, QuizUpdate


async def create_quiz(quiz_data: QuizCreate, current_user: User, session: AsyncSession) -> Quiz:
    course_repo = CourseRepository(session)
    course = await course_repo.get(quiz_data.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create quizzes for this course",
        )
    quiz_repo = QuizRepository(session)
    quiz = await quiz_repo.create(
        course_id=quiz_data.course_id,
        lesson_id=quiz_data.lesson_id,
        title=quiz_data.title,
        questions=quiz_data.questions,
        passing_score=quiz_data.passing_score,
    )
    return quiz


async def get_quiz(quiz_id: int, session: AsyncSession) -> Quiz:
    repo = QuizRepository(session)
    quiz = await repo.get(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    return quiz


async def list_quizzes(course_id: int, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[Quiz]:
    course_repo = CourseRepository(session)
    course = await course_repo.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    repo = QuizRepository(session)
    return await repo.get_by_course(course_id, skip=skip, limit=limit)


async def update_quiz(
    quiz_id: int, quiz_data: QuizUpdate, current_user: User, session: AsyncSession
) -> Quiz:
    quiz = await get_quiz(quiz_id, session)
    course_repo = CourseRepository(session)
    course = await course_repo.get(quiz.course_id)
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this quiz",
        )
    repo = QuizRepository(session)
    update_data = quiz_data.model_dump(exclude_unset=True)
    return await repo.update(quiz, **update_data)


async def delete_quiz(quiz_id: int, current_user: User, session: AsyncSession) -> None:
    quiz = await get_quiz(quiz_id, session)
    course_repo = CourseRepository(session)
    course = await course_repo.get(quiz.course_id)
    if current_user.role != UserRole.admin and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this quiz",
        )
    repo = QuizRepository(session)
    await repo.delete(quiz)


def calculate_score(questions: list[Any], answers: list[Any]) -> float:
    if not questions:
        return 0.0
    correct = 0
    for i, question in enumerate(questions):
        if i < len(answers):
            correct_answer = question.get("correct_answer") if isinstance(question, dict) else None
            student_answer = answers[i]
            if correct_answer is not None and student_answer == correct_answer:
                correct += 1
    return (correct / len(questions)) * 100.0


async def submit_attempt(
    quiz_id: int, answers: list[Any], student: User, session: AsyncSession
) -> QuizAttempt:
    quiz = await get_quiz(quiz_id, session)
    score = calculate_score(quiz.questions, answers)
    passed = score >= quiz.passing_score
    attempt_repo = QuizAttemptRepository(session)
    attempt = await attempt_repo.create(
        quiz_id=quiz_id,
        student_id=student.id,
        score=score,
        passed=passed,
    )
    return attempt


async def get_attempt_results(quiz_id: int, student: User, session: AsyncSession) -> list[QuizAttempt]:
    await get_quiz(quiz_id, session)
    repo = QuizAttemptRepository(session)
    return await repo.get_by_quiz_and_student(quiz_id, student.id)
