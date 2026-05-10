"""
AnalysisResult Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import AnalysisResult
from .base_repository import BaseRepository


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """분석 결과 Repository"""

    def __init__(self, session: Session):
        super().__init__(AnalysisResult, session)

    def get_by_experiment(self, experiment_id: str) -> Optional[AnalysisResult]:
        """
        실험별 분석 결과 조회 (최신)

        Args:
            experiment_id: 실험 ID

        Returns:
            분석 결과 또는 None
        """
        return (
            self.session.query(AnalysisResult)
            .filter(AnalysisResult.experiment_id == experiment_id)
            .order_by(AnalysisResult.created_at.desc())
            .first()
        )

    def get_all_by_experiment(self, experiment_id: str) -> List[AnalysisResult]:
        """
        실험별 모든 분석 결과 조회

        Args:
            experiment_id: 실험 ID

        Returns:
            분석 결과 리스트
        """
        return (
            self.session.query(AnalysisResult)
            .filter(AnalysisResult.experiment_id == experiment_id)
            .order_by(AnalysisResult.created_at.desc())
            .all()
        )
