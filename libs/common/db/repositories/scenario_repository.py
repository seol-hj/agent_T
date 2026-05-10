"""
Scenario Repository
"""

from typing import List
from sqlalchemy.orm import Session

from ..models import Scenario
from .base_repository import BaseRepository


class ScenarioRepository(BaseRepository[Scenario]):
    """시나리오 Repository"""

    def __init__(self, session: Session):
        super().__init__(Scenario, session)

    def get_by_experiment(self, experiment_id: str) -> List[Scenario]:
        """
        실험별 시나리오 조회

        Args:
            experiment_id: 실험 ID

        Returns:
            시나리오 리스트
        """
        return self.session.query(Scenario).filter(Scenario.experiment_id == experiment_id).all()

    def get_by_type(self, experiment_id: str, scenario_type: str) -> List[Scenario]:
        """
        실험 및 타입별 시나리오 조회

        Args:
            experiment_id: 실험 ID
            scenario_type: 시나리오 타입

        Returns:
            시나리오 리스트
        """
        return (
            self.session.query(Scenario)
            .filter(Scenario.experiment_id == experiment_id, Scenario.scenario_type == scenario_type)
            .all()
        )
