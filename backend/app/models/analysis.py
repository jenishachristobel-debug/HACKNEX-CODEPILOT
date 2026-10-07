from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    affected_files_json = Column(Text, default="[]")
    affected_functions_json = Column(Text, default="[]")
    evidence_json = Column(Text, default="[]")
    proposed_plan_json = Column(Text, default="[]")
    potential_side_effects_json = Column(Text, default="[]")
    uncertainties_json = Column(Text, default="[]")
    call_path = Column(Text, default="")
    expected_behavior = Column(Text, default="")
    actual_behavior = Column(Text, default="")
    proposed_fix = Column(Text, default="")
    is_llm_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="analysis")

