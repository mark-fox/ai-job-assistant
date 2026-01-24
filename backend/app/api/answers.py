import logging

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.job_assistant import generate_interview_answer
from app.core.db import get_db
from app.models import InterviewAnswer, ResumeAnalysis, User
from app.schemas import GenerateAnswerRequest, InterviewAnswerRead
from app.core.config import settings

router = APIRouter(
    prefix="/api",
    tags=["answers"],
)

logger = logging.getLogger("ai_job_assistant.answers")


@router.post(
    "/generate/answer",
    response_model=InterviewAnswerRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_answer(
    payload: GenerateAnswerRequest,
    db: Session = Depends(get_db),
) -> InterviewAnswerRead:
    user = None
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            logger.warning("generate answer for missing user_id=%s", payload.user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

    resume_analysis = None
    if payload.resume_analysis_id is not None:
        resume_analysis = (
            db.query(ResumeAnalysis)
            .filter(ResumeAnalysis.id == payload.resume_analysis_id)
            .first()
        )
        if not resume_analysis:
            logger.warning(
                "generate answer for missing resume_analysis_id=%s",
                payload.resume_analysis_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume analysis not found.",
            )

    if payload.user_id is not None and resume_analysis is not None:
        if resume_analysis.user_id is not None and resume_analysis.user_id != payload.user_id:
            logger.warning(
                "generate answer with mismatched user and resume analysis "
                "user_id=%s resume_analysis_id=%s resume_analysis_user_id=%s",
                payload.user_id,
                payload.resume_analysis_id,
                resume_analysis.user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume analysis does not belong to the specified user.",
            )

    answer_text = generate_interview_answer(
        question=payload.question,
        job_title=payload.job_title,
        company_name=payload.company_name,
    )

    interview_answer = InterviewAnswer(
        user_id=payload.user_id,
        resume_analysis_id=payload.resume_analysis_id,
        question=payload.question,
        job_title=payload.job_title,
        company_name=payload.company_name,
        answer=answer_text,
    )

    db.add(interview_answer)
    try:
        db.commit()
        db.refresh(interview_answer)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(
            "failed to generate answer user_id=%s resume_analysis_id=%s error=%s",
            payload.user_id,
            payload.resume_analysis_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate interview answer.",
        )

    logger.info(
        "generated interview answer id=%s user_id=%s resume_analysis_id=%s",
        interview_answer.id,
        interview_answer.user_id,
        interview_answer.resume_analysis_id,
    )

    return InterviewAnswerRead(
        id=interview_answer.id,
        user_id=interview_answer.user_id,
        resume_analysis_id=interview_answer.resume_analysis_id,
        question=interview_answer.question,
        job_title=interview_answer.job_title,
        company_name=interview_answer.company_name,
        answer=interview_answer.answer,
        created_at=interview_answer.created_at,
        provider=settings.llm_provider,
    )


@router.get(
    "/answers",
    response_model=List[InterviewAnswerRead],
)
def list_answers(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[InterviewAnswerRead]:
    answers = (
        db.query(InterviewAnswer)
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
            provider=settings.llm_provider,
        )
        for a in answers
    ]


@router.get(
    "/answers/{answer_id}",
    response_model=InterviewAnswerRead,
)
def get_answer(
    answer_id: int,
    db: Session = Depends(get_db),
) -> InterviewAnswerRead:
    answer = (
        db.query(InterviewAnswer)
        .filter(InterviewAnswer.id == answer_id)
        .first()
    )
    if not answer:
        logger.warning("interview answer not found id=%s", answer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview answer not found.",
        )
    return InterviewAnswerRead(
        id=answer.id,
        user_id=answer.user_id,
        resume_analysis_id=answer.resume_analysis_id,
        question=answer.question,
        job_title=answer.job_title,
        company_name=answer.company_name,
        answer=answer.answer,
        created_at=answer.created_at,
        provider=settings.llm_provider,
    )

