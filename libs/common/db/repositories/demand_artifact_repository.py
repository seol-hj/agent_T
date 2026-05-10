"""
DemandArtifact Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import DemandArtifact
from .base_repository import BaseRepository


class DemandArtifactRepository(BaseRepository[DemandArtifact]):
    """수요 산출물 Repository"""

    def __init__(self, session: Session):
        super().__init__(DemandArtifact, session)

    def get_by_scenario(self, scenario_id: str) -> List[DemandArtifact]:
        """
        시나리오별 수요 산출물 조회

        Args:
            scenario_id: 시나리오 ID

        Returns:
            수요 산출물 리스트
        """
        return self.session.query(DemandArtifact).filter(DemandArtifact.scenario_id == scenario_id).all()

    def get_by_variant(self, scenario_id: str, variant_id: str) -> Optional[DemandArtifact]:
        """
        시나리오 및 변형별 수요 산출물 조회

        Args:
            scenario_id: 시나리오 ID
            variant_id: 변형 ID

        Returns:
            수요 산출물 또는 None
        """
        return (
            self.session.query(DemandArtifact)
            .filter(DemandArtifact.scenario_id == scenario_id, DemandArtifact.variant_id == variant_id)
            .first()
        )
