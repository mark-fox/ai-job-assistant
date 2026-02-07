from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth import get_current_user_optional
from app.models.user import User
from app.models.resume_analysis import ResumeAnalysis
from app.models.interview_answer import InterviewAnswer

router = APIRouter()


class MetricsSummary(BaseModel):
    total_users: int
    total_resume_analyses: int
    total_answers: int
    user_resume_analyses: Optional[int] = None
    user_answers: Optional[int] = None


class UserMetricsSummary(BaseModel):
    user_id: int
    resume_analyses: int
    answers: int


@router.get("/summary", response_model=MetricsSummary)
def get_metrics_summary(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> MetricsSummary:
    total_users = db.query(User).count()
    total_resume_analyses = db.query(ResumeAnalysis).count()
    total_answers = db.query(InterviewAnswer).count()

    user_resume_analyses: Optional[int] = None
    user_answers: Optional[int] = None

    if current_user is not None:
        user_resume_analyses = (
            db.query(ResumeAnalysis)
            .filter(ResumeAnalysis.user_id == current_user.id)
            .count()
        )
        user_answers = (
            db.query(InterviewAnswer)
            .filter(InterviewAnswer.user_id == current_user.id)
            .count()
        )

    return MetricsSummary(
        total_users=total_users,
        total_resume_analyses=total_resume_analyses,
        total_answers=total_answers,
        user_resume_analyses=user_resume_analyses,
        user_answers=user_answers,
    )


@router.get("/user", response_model=UserMetricsSummary)
def get_user_metrics(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> UserMetricsSummary:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to fetch user metrics.",
        )

    resume_count = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == current_user.id)
        .count()
    )
    answer_count = (
        db.query(InterviewAnswer)
        .filter(InterviewAnswer.user_id == current_user.id)
        .count()
    )

    return UserMetricsSummary(
        user_id=current_user.id,
        resume_analyses=resume_count,
        answers=answer_count,
    )