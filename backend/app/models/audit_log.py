from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    actor = Column(String(50), default="system")
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="audit_logs")
    project = relationship("Project", back_populates="audit_logs")

