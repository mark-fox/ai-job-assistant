import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.job_assistant import summarize_resume
from app.core.db import get_db
from app.models import ResumeAnalysis, User
from app.schemas import ResumeAnalyzeRequest, ResumeAnalysisRead
from app.core.config import settings

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
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
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
    try:
        db.commit()
        db.refresh(analysis)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(
            "failed to create resume analysis user_id=%s error=%s",
            payload.user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not analyze resume.",
        )

    logger.info("created resume analysis id=%s user_id=%s", analysis.id, analysis.user_id)

    return ResumeAnalysisRead(
        id=analysis.id,
        user_id=analysis.user_id,
        resume_text=analysis.resume_text,
        summary=analysis.summary,
        created_at=analysis.created_at,
        provider=settings.llm_provider,
    )


@router.get(
    "/{analysis_id}",
    response_model=ResumeAnalysisRead,
)
def get_resume_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
) -> ResumeAnalysisRead:
    analysis = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.id == analysis_id)
        .first()
    )
    if not analysis:
        logger.warning("resume analysis not found id=%s", analysis_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis not found.",
        )
    return ResumeAnalysisRead(
        id=analysis.id,
        user_id=analysis.user_id,
        resume_text=analysis.resume_text,
        summary=analysis.summary,
        created_at=analysis.created_at,
        provider=settings.llm_provider,
    )

