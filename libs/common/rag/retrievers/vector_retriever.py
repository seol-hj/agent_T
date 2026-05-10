"""
Vector Retriever (Placeholder)

벡터 DB 기반 RAG 검색 (향후 구현)
"""

from typing import List, Optional

from .retriever import Retriever
from ..schemas import RAGContext, Document


class VectorRetriever(Retriever):
    """
    벡터 DB 기반 Retriever (Placeholder)

    향후 구현:
    - OpenSearch Vector 검색
    - Qdrant 통합
    - 임베딩 모델 (Bedrock Titan Embeddings 등)
    - 코사인 유사도 기반 검색
    """

    def __init__(
        self,
        vector_db_type: str = "opensearch",
        embedding_model: str = "bedrock-titan-embeddings",
    ):
        """
        Args:
            vector_db_type: 벡터 DB 타입 (opensearch / qdrant)
            embedding_model: 임베딩 모델
        """
        self.vector_db_type = vector_db_type
        self.embedding_model = embedding_model

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> List[RAGContext]:
        raise NotImplementedError(
            "VectorRetriever is not yet implemented. "
            "Use InMemoryRetriever for now."
        )

    async def add_document(self, document: Document) -> None:
        raise NotImplementedError("VectorRetriever is not yet implemented.")

    async def remove_document(self, document_id: str) -> None:
        raise NotImplementedError("VectorRetriever is not yet implemented.")

    async def get_document(self, document_id: str) -> Optional[Document]:
        raise NotImplementedError("VectorRetriever is not yet implemented.")

    async def list_documents(self) -> List[Document]:
        raise NotImplementedError("VectorRetriever is not yet implemented.")
