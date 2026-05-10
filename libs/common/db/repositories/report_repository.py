"""
Report Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import Report
from .base_repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """리포트 Repository"""

    def __init__(self, session: Session):
        super().__init__(Report, session)

    def get_by_experiment(self, experiment_id: str) -> List[Report]:
        """
        실험별 리포트 조회

        Args:
            experiment_id: 실험 ID

        Returns:
            리포트 리스트
        """
        return (
            self.session.query(Report)
            .filter(Report.experiment_id == experiment_id)
            .order_by(Report.created_at.desc())
            .all()
        )

    def get_by_type(self, experiment_id: str, report_type: str) -> Optional[Report]:
        """
        실험 및 타입별 리포트 조회 (최신)

        Args:
            experiment_id: 실험 ID
            report_type: 리포트 타입 (template, llm)

        Returns:
            리포트 또는 None
        """
        return (
            self.session.query(Report)
            .filter(Report.experiment_id == experiment_id, Report.report_type == report_type)
            .order_by(Report.created_at.desc())
            .first()
        )

    def get_recent(self, limit: int = 20) -> List[Report]:
        """
        최근 리포트 조회

        Args:
            limit: 최대 개수

        Returns:
            리포트 리스트
        """
        return (
            self.session.query(Report)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )
