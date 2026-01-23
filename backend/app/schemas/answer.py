from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class GenerateAnswerRequest(BaseModel):
    user_id: int | None = None
    resume_analysis_id: int | None = None
    question: str = Field(min_length=5)
    job_title: str | None = Field(default=None, max_length=100)
    company_name: str | None = Field(default=None, max_length=100)


class InterviewAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    resume_analysis_id: int | None
    question: str
    job_title: str | None
    company_name: str | None
    answer: str
    created_at: datetime
