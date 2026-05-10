"""
Experiment Repository
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import Experiment
from .base_repository import BaseRepository


class ExperimentRepository(BaseRepository[Experiment]):
    """실험 Repository"""

    def __init__(self, session: Session):
        super().__init__(Experiment, session)

    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[Experiment]:
        """
        상태별 실험 조회

        Args:
            status: 실험 상태 (pending, running, completed, failed)
            limit: 최대 개수

        Returns:
            실험 리스트
        """
        query = self.session.query(Experiment).filter(Experiment.status == status)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_recent(self, limit: int = 10) -> List[Experiment]:
        """
        최근 실험 조회

        Args:
            limit: 최대 개수

        Returns:
            실험 리스트
        """
        return (
            self.session.query(Experiment)
            .order_by(Experiment.created_at.desc())
            .limit(limit)
            .all()
        )

    def update_status(
        self,
        id: str,
        status: str,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ) -> Optional[Experiment]:
        """
        실험 상태 업데이트

        Args:
            id: 실험 ID
            status: 새 상태
            error_message: 에러 메시지 (실패 시)
            completed_at: 완료 시간

        Returns:
            업데이트된 실험 또는 None
        """
        experiment = self.get(id)
        if experiment is None:
            return None

        experiment.status = status
        if error_message is not None:
            experiment.error_message = error_message
        if completed_at is not None:
            experiment.completed_at = completed_at

        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def get_with_relations(self, id: str) -> Optional[Experiment]:
        """
        관계 데이터를 포함한 실험 조회

        Args:
            id: 실험 ID

        Returns:
            실험 (user_request, experiment_spec, scenarios, simulation_runs, analysis_results, reports 포함)
        """
        return (
            self.session.query(Experiment)
            .filter(Experiment.id == id)
            .first()
        )
