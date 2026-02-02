import logging

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.job_assistant import summarize_resume
from app.core.db import get_db
from app.models import ResumeAnalysis, User, InterviewAnswer
from app.schemas import ResumeAnalyzeRequest, ResumeAnalysisRead, InterviewAnswerRead
from app.core.config import settings
from app.core.auth import get_current_user_optional

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
    current_user: User | None = Depends(get_current_user_optional),
) -> ResumeAnalysisRead:
    if current_user is not None and payload.user_id is not None:
        if current_user.id != payload.user_id:
            logger.warning(
                "analyze resume with mismatched header and body user "
                "header_user_id=%s body_user_id=%s",
                current_user.id,
                payload.user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Body user_id does not match authenticated user.",
            )

    if current_user is not None and payload.user_id is None:
        payload.user_id = current_user.id

    user = None
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            logger.warning("resume analysis for missing user_id=%s", payload.user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

    summary_text, provider_used = summarize_resume(payload.resume_text)

    analysis = ResumeAnalysis(
        user_id=payload.user_id,
        resume_text=payload.resume_text,
        summary=summary_text,
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
        provider=provider_used,
    )


@router.get(
    "",
    response_model=List[ResumeAnalysisRead],
)
def list_resume_analyses(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int | None = Query(default=None, ge=1),
) -> List[ResumeAnalysisRead]:
    query = db.query(ResumeAnalysis)

    if user_id is not None:
        query = query.filter(ResumeAnalysis.user_id == user_id)

    analyses = (
        query
        .order_by(ResumeAnalysis.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


    return [
        ResumeAnalysisRead(
            id=a.id,
            user_id=a.user_id,
            resume_text=a.resume_text,
            summary=a.summary,
            created_at=a.created_at,
            provider=settings.llm_provider,
        )
        for a in analyses
    ]


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


@router.get(
    "/{analysis_id}/answers",
    response_model=List[InterviewAnswerRead],
)
def list_answers_for_resume(
    analysis_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[InterviewAnswerRead]:
    analysis = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.id == analysis_id)
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis not found.",
        )

    answers = (
        db.query(InterviewAnswer)
        .filter(InterviewAnswer.resume_analysis_id == analysis_id)
        .order_by(InterviewAnswer.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        InterviewAnswerRead(
            id=a.id,
            user_id=a.user_id,
            resume_analysis_id=a.resume_analysis_id,
            question=a.question,
            job_title=a.job_title,
            company_name=a.company_name,
            answer=a.answer,
            created_at=a.created_at,
            # For list-style endpoints, provider reflects the currently configured provider.
            provider=settings.llm_provider,
        )
        for a in answers
    ]
