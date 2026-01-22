import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import InterviewAnswer, ResumeAnalysis, User
from app.schemas import GenerateAnswerRequest, InterviewAnswerRead

router = APIRouter(
    prefix="/api",
    tags=["answers"],
)

logger = logging.getLogger("ai_job_assistant.answers")


def _simple_answer(
    question: str,
    job_title: str | None,
    company_name: str | None,
) -> str:
    parts: list[str] = [f"Question: {question}"]

    if job_title:
        parts.append(f"Target role: {job_title}")
    if company_name:
        parts.append(f"Company: {company_name}")

    parts.append(
        "This is a placeholder answer for development purposes, "
        "not a final AI-generated response."
    )

    return " | ".join(parts)


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

    answer_text = _simple_answer(
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
    db.commit()
    db.refresh(interview_answer)

    logger.info(
        "generated interview answer id=%s user_id=%s resume_analysis_id=%s",
        interview_answer.id,
        interview_answer.user_id,
        interview_answer.resume_analysis_id,
    )

    return interview_answer
