from datetime import datetime

from pydantic import BaseModel


class GenerateAnswerRequest(BaseModel):
    user_id: int | None = None
    resume_analysis_id: int | None = None
    question: str
    job_title: str | None = None
    company_name: str | None = None


class InterviewAnswerRead(BaseModel):
    id: int
    user_id: int | None
    resume_analysis_id: int | None
    question: str
    job_title: str | None
    company_name: str | None
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True
