import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import ResumeAnalysis, User
from app.schemas import ResumeAnalyzeRequest, ResumeAnalysisRead
from app.agents.job_assistant import summarize_resume

router = APIRouter(
    prefix="/api/resume",
    tags=["resume"],
)

logger = logging.getLogger("ai_job_assistant.resume")


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

    summary = summarize_resume(payload.resume_text)

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
