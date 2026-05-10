"""
UserRequest Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import UserRequest
from .base_repository import BaseRepository


class UserRequestRepository(BaseRepository[UserRequest]):
    """사용자 요청 Repository"""

    def __init__(self, session: Session):
        super().__init__(UserRequest, session)

    def get_by_user(self, user_id: str, limit: Optional[int] = None) -> List[UserRequest]:
        """
        사용자별 요청 조회

        Args:
            user_id: 사용자 ID
            limit: 최대 개수

        Returns:
            요청 리스트
        """
        query = self.session.query(UserRequest).filter(UserRequest.user_id == user_id)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def search_by_text(self, search_text: str, limit: int = 20) -> List[UserRequest]:
        """
        텍스트 검색

        Args:
            search_text: 검색어
            limit: 최대 개수

        Returns:
            요청 리스트
        """
        return (
            self.session.query(UserRequest)
            .filter(UserRequest.request_text.contains(search_text))
            .order_by(UserRequest.created_at.desc())
            .limit(limit)
            .all()
        )
