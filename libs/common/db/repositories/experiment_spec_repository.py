"""
ExperimentSpec Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import ExperimentSpec
from .base_repository import BaseRepository


class ExperimentSpecRepository(BaseRepository[ExperimentSpec]):
    """실험 명세 Repository"""

    def __init__(self, session: Session):
        super().__init__(ExperimentSpec, session)

    def get_by_model_version(self, model_version_id: str, limit: Optional[int] = None) -> List[ExperimentSpec]:
        """
        모델 버전별 명세 조회

        Args:
            model_version_id: 모델 버전 ID
            limit: 최대 개수

        Returns:
            명세 리스트
        """
        query = self.session.query(ExperimentSpec).filter(
            ExperimentSpec.model_version_id == model_version_id
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_high_confidence(self, min_confidence: float = 0.8, limit: int = 20) -> List[ExperimentSpec]:
        """
        고신뢰도 명세 조회

        Args:
            min_confidence: 최소 신뢰도
            limit: 최대 개수

        Returns:
            명세 리스트
        """
        return (
            self.session.query(ExperimentSpec)
            .filter(ExperimentSpec.confidence_score >= min_confidence)
            .order_by(ExperimentSpec.confidence_score.desc())
            .limit(limit)
            .all()
        )
