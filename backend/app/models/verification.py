from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    classification = Column(String(50), nullable=False)  # FIX_VERIFIED, REGRESSION_DETECTED, PARTIALLY_VERIFIED, VERIFICATION_FAILED, NOT_EXECUTED, NEEDS_REVIEW
    functional_status = Column(String(50), default="NOT_EXECUTED")
    regression_status = Column(String(50), default="NOT_EXECUTED")
    syntax_status = Column(String(50), default="PASSED")
    security_status = Column(String(50), default="PASSED")
    evidence_summary_json = Column(Text, default="{}")
    integrity_check_json = Column(Text, default="{}")
    markdown_report = Column(Text, default="")
    json_report = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="verification_report")

