from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class FixHistory(Base):
    __tablename__ = "fix_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)
    project_name = Column(String(255), nullable=False)
    bug_title = Column(String(255), nullable=False)
    root_cause_summary = Column(Text, nullable=True)
    target_file = Column(String(500), nullable=True)
    patch_summary = Column(Text, nullable=True)
    outcome = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

