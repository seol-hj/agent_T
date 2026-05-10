"""
ModelVersion Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import ModelVersion
from .base_repository import BaseRepository


class ModelVersionRepository(BaseRepository[ModelVersion]):
    """모델 버전 Repository"""

    def __init__(self, session: Session):
        super().__init__(ModelVersion, session)

    def get_active(self) -> List[ModelVersion]:
        """
        활성 모델 버전 조회

        Returns:
            모델 버전 리스트
        """
        return self.session.query(ModelVersion).filter(ModelVersion.is_active == True).all()

    def get_by_name(self, model_name: str) -> List[ModelVersion]:
        """
        모델명별 버전 조회

        Args:
            model_name: 모델명

        Returns:
            모델 버전 리스트
        """
        return (
            self.session.query(ModelVersion)
            .filter(ModelVersion.model_name == model_name)
            .order_by(ModelVersion.created_at.desc())
            .all()
        )

    def get_by_provider(self, model_provider: str) -> List[ModelVersion]:
        """
        제공자별 모델 버전 조회

        Args:
            model_provider: 제공자 (bedrock, openai, etc.)

        Returns:
            모델 버전 리스트
        """
        return (
            self.session.query(ModelVersion)
            .filter(ModelVersion.model_provider == model_provider)
            .order_by(ModelVersion.created_at.desc())
            .all()
        )

    def deactivate(self, id: str) -> Optional[ModelVersion]:
        """
        모델 버전 비활성화

        Args:
            id: 모델 버전 ID

        Returns:
            비활성화된 모델 버전 또는 None
        """
        return self.update(id, is_active=False)

    def activate(self, id: str) -> Optional[ModelVersion]:
        """
        모델 버전 활성화

        Args:
            id: 모델 버전 ID

        Returns:
            활성화된 모델 버전 또는 None
        """
        return self.update(id, is_active=True)
