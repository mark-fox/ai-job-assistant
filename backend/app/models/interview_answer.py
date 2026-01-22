from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.db import Base


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    resume_analysis_id = Column(
        Integer,
        ForeignKey("resume_analyses.id"),
        nullable=True,
        index=True,
    )
    question = Column(Text, nullable=False)
    job_title = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    answer = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
