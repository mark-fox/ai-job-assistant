from datetime import datetime

from pydantic import BaseModel


class ResumeAnalyzeRequest(BaseModel):
    user_id: int | None = None
    resume_text: str


class ResumeAnalysisRead(BaseModel):
    id: int
    user_id: int | None
    resume_text: str
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True
