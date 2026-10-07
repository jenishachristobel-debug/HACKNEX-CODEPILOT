from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    bug_title = Column(String(255), nullable=False)
    bug_description = Column(Text, nullable=False)
    error_traceback = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    reproduction_steps = Column(Text, nullable=True)
    mode = Column(String(50), default="patch_and_verify")  # analysis_only, patch_proposal, patch_and_verify
    status = Column(String(50), default="pending")
    current_attempt = Column(Integer, default=1)
    max_attempts = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    analysis = relationship("AnalysisResult", back_populates="task", uselist=False, cascade="all, delete-orphan")
    patches = relationship("Patch", back_populates="task", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="task", cascade="all, delete-orphan")
    verification_report = relationship("VerificationReport", back_populates="task", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="task", cascade="all, delete-orphan")

