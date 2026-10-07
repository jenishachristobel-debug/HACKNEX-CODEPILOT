from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class TestRun(Base):
    __tablename__ = "test_runs"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    attempt_number = Column(Integer, default=1)
    stage = Column(String(50), nullable=False)  # baseline, post_patch, regression_generated
    command = Column(String(500), nullable=False)
    exit_code = Column(BigInteger, default=0)

    duration_ms = Column(Integer, default=0)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    output_log = Column(Text, default="")
    test_details_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="test_runs")

