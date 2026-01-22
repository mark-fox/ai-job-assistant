import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import ResumeAnalysis, User
from app.schemas import ResumeAnalyzeRequest, ResumeAnalysisRead

router = APIRouter(
    prefix="/api/resume",
    tags=["resume"],
)

logger = logging.getLogger("ai_job_assistant.resume")

def _simple_resume_summary(resume_text: str) -> str:
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    word_count = len(resume_text.split())
    line_count = len(lines)

    return (
        f"Basic analysis only. Approximate word count: {word_count}. "
        f"Non-empty line count: {line_count}."
    )


@router.post(
    "/analyze",
    response_model=ResumeAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
def analyze_resume(
    payload: ResumeAnalyzeRequest,
    db: Session = Depends(get_db),
) -> ResumeAnalysisRead:
    user = None
    if payload.user_id is not None and not user:
        logger.warning("resume analysis for missing user_id=%s", payload.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    summary = _simple_resume_summary(payload.resume_text)

    analysis = ResumeAnalysis(
        user_id=payload.user_id,
        resume_text=payload.resume_text,
        summary=summary,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    logger.info("created resume analysis id=%s user_id=%s", analysis.id, analysis.user_id)

    return analysis
