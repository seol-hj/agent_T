"""
Database Models
"""
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class PipelineExecution(Base):
    """파이프라인 실행 이력"""
    __tablename__ = "pipeline_executions"

    execution_id = Column(String, primary_key=True)
    request_id = Column(String, nullable=False)
    experiment_id = Column(String)
    status = Column(String, nullable=False)  # running, completed, failed, partial
    steps = Column(JSON, nullable=False, default=list)
    report_uri = Column(String)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    total_duration_ms = Column(String)

    def to_dict(self):
        """PipelineExecutionResult로 변환"""
        return {
            "schema_version": "1.0",
            "execution_id": self.execution_id,
            "request_id": self.request_id,
            "experiment_id": self.experiment_id or "",
            "status": self.status,
            "steps": self.steps or [],
            "report_uri": self.report_uri,
            "started_at": self.started_at.isoformat() if self.started_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": float(self.total_duration_ms) if self.total_duration_ms else None,
            "error_message": self.error_message,
        }
