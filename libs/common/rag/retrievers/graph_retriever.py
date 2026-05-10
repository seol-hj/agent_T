"""
Graph Retriever (Placeholder)

그래프 DB 기반 RAG 검색 (향후 구현)
"""

from typing import List, Optional

from .retriever import Retriever
from ..schemas import RAGContext, Document


class GraphRetriever(Retriever):
    """
    그래프 DB 기반 Retriever (Placeholder)

    향후 구현:
    - Neo4j 통합
    - 문서 간 관계 그래프
    - 엔티티 추출 및 연결
    - 그래프 쿼리 기반 검색
    """

    def __init__(self, graph_db_uri: str, username: str, password: str):
        """
        Args:
            graph_db_uri: 그래프 DB URI (예: bolt://localhost:7687)
            username: 사용자 이름
            password: 비밀번호
        """
        self.graph_db_uri = graph_db_uri
        self.username = username
        self.password = password

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> List[RAGContext]:
        raise NotImplementedError(
            "GraphRetriever is not yet implemented. "
            "Use InMemoryRetriever for now."
        )

    async def add_document(self, document: Document) -> None:
        raise NotImplementedError("GraphRetriever is not yet implemented.")

    async def remove_document(self, document_id: str) -> None:
        raise NotImplementedError("GraphRetriever is not yet implemented.")

    async def get_document(self, document_id: str) -> Optional[Document]:
        raise NotImplementedError("GraphRetriever is not yet implemented.")

    async def list_documents(self) -> List[Document]:
        raise NotImplementedError("GraphRetriever is not yet implemented.")
