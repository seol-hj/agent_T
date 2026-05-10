"""
RAGDocument Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import RAGDocument
from .base_repository import BaseRepository


class RAGDocumentRepository(BaseRepository[RAGDocument]):
    """RAG 문서 Repository"""

    def __init__(self, session: Session):
        super().__init__(RAGDocument, session)

    def get_active(self) -> List[RAGDocument]:
        """
        활성 문서 조회

        Returns:
            문서 리스트
        """
        return self.session.query(RAGDocument).filter(RAGDocument.is_active == True).all()

    def get_by_category(self, category: str) -> List[RAGDocument]:
        """
        카테고리별 문서 조회

        Args:
            category: 카테고리 (policy, technical, case_study, etc.)

        Returns:
            문서 리스트
        """
        return (
            self.session.query(RAGDocument)
            .filter(RAGDocument.category == category, RAGDocument.is_active == True)
            .order_by(RAGDocument.created_at.desc())
            .all()
        )

    def search_by_text(self, search_text: str, limit: int = 20) -> List[RAGDocument]:
        """
        텍스트 검색

        Args:
            search_text: 검색어
            limit: 최대 개수

        Returns:
            문서 리스트
        """
        return (
            self.session.query(RAGDocument)
            .filter(
                RAGDocument.is_active == True,
                RAGDocument.content_text.contains(search_text)
            )
            .order_by(RAGDocument.created_at.desc())
            .limit(limit)
            .all()
        )

    def search_by_title(self, search_text: str, limit: int = 20) -> List[RAGDocument]:
        """
        제목 검색

        Args:
            search_text: 검색어
            limit: 최대 개수

        Returns:
            문서 리스트
        """
        return (
            self.session.query(RAGDocument)
            .filter(
                RAGDocument.is_active == True,
                RAGDocument.title.contains(search_text)
            )
            .order_by(RAGDocument.created_at.desc())
            .limit(limit)
            .all()
        )

    def deactivate(self, id: str) -> Optional[RAGDocument]:
        """
        문서 비활성화

        Args:
            id: 문서 ID

        Returns:
            비활성화된 문서 또는 None
        """
        return self.update(id, is_active=False)

    def activate(self, id: str) -> Optional[RAGDocument]:
        """
        문서 활성화

        Args:
            id: 문서 ID

        Returns:
            활성화된 문서 또는 None
        """
        return self.update(id, is_active=True)
