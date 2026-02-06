from typing import Optional

from fastapi import APIRouter, Depends
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