from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ResumeAnalyzeRequest(BaseModel):
    user_id: int | None = None
    resume_text: str = Field(min_length=20)


class ResumeAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    resume_text: str
    summary: str
    created_at: datetime
