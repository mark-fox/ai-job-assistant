from enum import Enum
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("ai_job_assistant.agent")


class LLMProvider(str, Enum):
    STUB = "stub"
    OPENAI = "openai"


def summarize_resume(resume_text: str) -> str:
    provider = _get_provider()

    if provider is LLMProvider.STUB:
        return _summarize_resume_stub(resume_text)

    if provider is LLMProvider.OPENAI:
        return _summarize_resume_stub(resume_text)

    logger.warning("unknown llm provider %s, falling back to stub", settings.llm_provider)
    return _summarize_resume_stub(resume_text)


def generate_interview_answer(
    question: str,
    job_title: Optional[str] = None,
    company_name: Optional[str] = None,
) -> str:
    provider = _get_provider()

    if provider is LLMProvider.STUB:
        return _generate_interview_answer_stub(
            question=question,
            job_title=job_title,
            company_name=company_name,
        )

    if provider is LLMProvider.OPENAI:
        return _generate_interview_answer_stub(
            question=question,
            job_title=job_title,
            company_name=company_name,
        )

    logger.warning("unknown llm provider %s, falling back to stub", settings.llm_provider)
    return _generate_interview_answer_stub(
        question=question,
        job_title=job_title,
        company_name=company_name,
    )


def _get_provider() -> LLMProvider:
    try:
        return LLMProvider(settings.llm_provider)
    except ValueError:
        logger.warning("invalid llm provider value %s", settings.llm_provider)
        return LLMProvider.STUB


def _summarize_resume_stub(resume_text: str) -> str:
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    word_count = len(resume_text.split())
    line_count = len(lines)

    return (
        f"Basic analysis only. Approximate word count: {word_count}. "
        f"Non-empty line count: {line_count}."
    )


def _generate_interview_answer_stub(
    question: str,
    job_title: Optional[str],
    company_name: Optional[str],
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
