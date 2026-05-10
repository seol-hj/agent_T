"""
SimulationRun Repository
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import SimulationRun
from .base_repository import BaseRepository


class SimulationRunRepository(BaseRepository[SimulationRun]):
    """시뮬레이션 실행 Repository"""

    def __init__(self, session: Session):
        super().__init__(SimulationRun, session)

    def get_by_experiment(self, experiment_id: str) -> List[SimulationRun]:
        """
        실험별 시뮬레이션 실행 조회

        Args:
            experiment_id: 실험 ID

        Returns:
            시뮬레이션 실행 리스트
        """
        return self.session.query(SimulationRun).filter(SimulationRun.experiment_id == experiment_id).all()

    def get_by_variant(self, experiment_id: str, variant_id: str) -> Optional[SimulationRun]:
        """
        실험 및 변형별 시뮬레이션 실행 조회

        Args:
            experiment_id: 실험 ID
            variant_id: 변형 ID

        Returns:
            시뮬레이션 실행 또는 None
        """
        return (
            self.session.query(SimulationRun)
            .filter(SimulationRun.experiment_id == experiment_id, SimulationRun.variant_id == variant_id)
            .first()
        )

    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[SimulationRun]:
        """
        상태별 시뮬레이션 실행 조회

        Args:
            status: 실행 상태
            limit: 최대 개수

        Returns:
            시뮬레이션 실행 리스트
        """
        query = self.session.query(SimulationRun).filter(SimulationRun.execution_status == status)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def update_status(
        self,
        id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        execution_time_ms: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Optional[SimulationRun]:
        """
        시뮬레이션 상태 업데이트

        Args:
            id: 시뮬레이션 ID
            status: 새 상태
            started_at: 시작 시간
            completed_at: 완료 시간
            execution_time_ms: 실행 시간 (ms)
            error_message: 에러 메시지

        Returns:
            업데이트된 시뮬레이션 또는 None
        """
        simulation = self.get(id)
        if simulation is None:
            return None

        simulation.execution_status = status
        if started_at is not None:
            simulation.started_at = started_at
        if completed_at is not None:
            simulation.completed_at = completed_at
        if execution_time_ms is not None:
            simulation.execution_time_ms = execution_time_ms
        if error_message is not None:
            simulation.error_message = error_message

        self.session.commit()
        self.session.refresh(simulation)
        return simulation
