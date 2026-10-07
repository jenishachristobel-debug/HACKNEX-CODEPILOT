from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RepositoryScan(Base):
    __tablename__ = "repository_scans"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    total_files = Column(Integer, default=0)
    python_files = Column(Integer, default=0)
    test_files = Column(Integer, default=0)
    syntax_errors_count = Column(Integer, default=0)
    dependencies_json = Column(Text, default="[]")
    manifest_json = Column(Text, default="{}")
    inventory_json = Column(Text, default="{}")
    dependency_graph_json = Column(Text, default="{}")
    file_tree_json = Column(Text, default="[]")
    symbols_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="scan")

