"""
Retriever Interface

RAG 컨텍스트 검색 추상화
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..schemas import RAGContext, Document


class Retriever(ABC):
    """
    RAG Retriever 인터페이스

    구현체:
    - InMemoryRetriever: 메모리 기반 키워드 검색 (초기 구현)
    - VectorRetriever: 벡터 DB 기반 검색 (OpenSearch, Qdrant 등)
    - GraphRetriever: 그래프 DB 기반 검색
    - BedrockKnowledgeBaseRetriever: AWS Bedrock Knowledge Base
    """

    @abstractmethod
    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> List[RAGContext]:
        """
        쿼리에 맞는 컨텍스트 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 컨텍스트 수
            filters: 추가 필터 (카테고리, 태그 등)

        Returns:
            RAGContext 리스트 (관련도 순)
        """
        pass

    @abstractmethod
    async def add_document(self, document: Document) -> None:
        """
        문서 추가

        Args:
            document: 추가할 문서
        """
        pass

    @abstractmethod
    async def remove_document(self, document_id: str) -> None:
        """
        문서 삭제

        Args:
            document_id: 삭제할 문서 ID
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        문서 조회

        Args:
            document_id: 문서 ID

        Returns:
            Document 또는 None
        """
        pass

    @abstractmethod
    async def list_documents(self) -> List[Document]:
        """
        모든 문서 목록 조회

        Returns:
            Document 리스트
        """
        pass
