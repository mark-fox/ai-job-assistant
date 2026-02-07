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
from app.core.auth import get_current_user_optional

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
    current_user: User | None = Depends(get_current_user_optional),
) -> InterviewAnswerRead:
    if current_user is not None and payload.user_id is not None:
        if current_user.id != payload.user_id:
            logger.warning(
                "generate answer with mismatched header and body user "
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

    resume_summary = resume_analysis.summary if resume_analysis is not None else None

    answer_text, provider_used = generate_interview_answer(
        question=payload.question,
        job_title=payload.job_title,
        company_name=payload.company_name,
        resume_summary=resume_summary,
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
        provider=provider_used,
    )


@router.get(
    "/answers",
    response_model=List[InterviewAnswerRead],
)
def list_answers(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int | None = Query(default=None, ge=1),
    current_user: User | None = Depends(get_current_user_optional),
) -> List[InterviewAnswerRead]:
    query = db.query(InterviewAnswer)

    # Resolve effective user_id using header + query rules
    effective_user_id = user_id

    if current_user is not None and user_id is not None:
        if current_user.id != user_id:
            logger.warning(
                "list answers with mismatched header and query "
                "header_user_id=%s query_user_id=%s",
                current_user.id,
                user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query user_id does not match authenticated user.",
            )

    if current_user is not None and user_id is None:
        effective_user_id = current_user.id

    if effective_user_id is not None:
        query = query.filter(InterviewAnswer.user_id == effective_user_id)

    answers = (
        query
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


@router.delete(
    "/answers/{answer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> None:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to delete interview answers.",
        )

    answer = (
        db.query(InterviewAnswer)
        .filter(InterviewAnswer.id == answer_id)
        .first()
    )

    if answer is None:
        logger.warning("interview answer not found for delete id=%s", answer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview answer not found.",
        )

    if answer.user_id is not None and answer.user_id != current_user.id:
        logger.warning(
            "forbidden delete interview answer id=%s header_user_id=%s answer_user_id=%s",
            answer_id,
            current_user.id,
            answer.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this interview answer.",
        )

    try:
        db.delete(answer)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(
            "failed to delete interview answer id=%s error=%s",
            answer_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete interview answer.",
        )

    logger.info(
        "deleted interview answer id=%s user_id=%s",
        answer.id,
        answer.user_id,
    )
    return None