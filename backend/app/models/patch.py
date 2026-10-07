from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Patch(Base):
    __tablename__ = "patches"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    attempt_number = Column(Integer, default=1)
    target_file = Column(String(500), nullable=False)
    original_code = Column(Text, nullable=False)
    new_code = Column(Text, nullable=False)
    diff = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    potential_impact = Column(Text, nullable=True)
    status = Column(String(50), default="proposed")  # proposed, approved, rejected, applied, reverted
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="patches")

