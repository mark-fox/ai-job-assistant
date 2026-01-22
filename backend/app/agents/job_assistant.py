from typing import Optional


def summarize_resume(resume_text: str) -> str:
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    word_count = len(resume_text.split())
    line_count = len(lines)

    return (
        f"Basic analysis only. Approximate word count: {word_count}. "
        f"Non-empty line count: {line_count}."
    )


def generate_interview_answer(
    question: str,
    job_title: Optional[str] = None,
    company_name: Optional[str] = None,
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
