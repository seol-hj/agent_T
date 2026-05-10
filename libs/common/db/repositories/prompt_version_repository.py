"""
PromptVersion Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import PromptVersion
from .base_repository import BaseRepository


class PromptVersionRepository(BaseRepository[PromptVersion]):
    """프롬프트 버전 Repository"""

    def __init__(self, session: Session):
        super().__init__(PromptVersion, session)

    def get_active(self) -> List[PromptVersion]:
        """
        활성 프롬프트 버전 조회

        Returns:
            프롬프트 버전 리스트
        """
        return self.session.query(PromptVersion).filter(PromptVersion.is_active == True).all()

    def get_by_name(self, prompt_name: str) -> List[PromptVersion]:
        """
        프롬프트명별 버전 조회

        Args:
            prompt_name: 프롬프트명

        Returns:
            프롬프트 버전 리스트
        """
        return (
            self.session.query(PromptVersion)
            .filter(PromptVersion.prompt_name == prompt_name)
            .order_by(PromptVersion.created_at.desc())
            .all()
        )

    def get_active_by_name(self, prompt_name: str) -> Optional[PromptVersion]:
        """
        활성 프롬프트 조회 (특정 이름)

        Args:
            prompt_name: 프롬프트명

        Returns:
            프롬프트 버전 또는 None
        """
        return (
            self.session.query(PromptVersion)
            .filter(PromptVersion.prompt_name == prompt_name, PromptVersion.is_active == True)
            .order_by(PromptVersion.created_at.desc())
            .first()
        )

    def get_by_type(self, prompt_type: str) -> List[PromptVersion]:
        """
        타입별 프롬프트 버전 조회

        Args:
            prompt_type: 프롬프트 타입 (system, user, assistant)

        Returns:
            프롬프트 버전 리스트
        """
        return (
            self.session.query(PromptVersion)
            .filter(PromptVersion.prompt_type == prompt_type)
            .order_by(PromptVersion.created_at.desc())
            .all()
        )

    def deactivate(self, id: str) -> Optional[PromptVersion]:
        """
        프롬프트 버전 비활성화

        Args:
            id: 프롬프트 버전 ID

        Returns:
            비활성화된 프롬프트 버전 또는 None
        """
        return self.update(id, is_active=False)

    def activate(self, id: str) -> Optional[PromptVersion]:
        """
        프롬프트 버전 활성화

        Args:
            id: 프롬프트 버전 ID

        Returns:
            활성화된 프롬프트 버전 또는 None
        """
        return self.update(id, is_active=True)
