"""
Vector Store Gateway (Placeholder)
Vector DB Provider 추상화 계층
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os


class VectorStoreGateway(ABC):
    """
    Vector Store Gateway Base Class

    RAG를 위한 Vector DB 추상화
    향후 Pinecone, Weaviate, ChromaDB 등 구현
    """

    @abstractmethod
    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        벡터 삽입/업데이트

        Args:
            vectors: 벡터 리스트
            ids: ID 리스트
            metadata: 메타데이터 리스트

        Returns:
            bool: 성공 여부
        """
        pass

    @abstractmethod
    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        유사도 검색

        Args:
            vector: 쿼리 벡터
            top_k: 반환 개수
            filter: 필터 조건

        Returns:
            List[Dict]: 검색 결과 [{id, score, metadata}]
        """
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """
        벡터 삭제

        Args:
            ids: 삭제할 ID 리스트

        Returns:
            bool: 성공 여부
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 이름"""
        pass


class MockVectorStoreProvider(VectorStoreGateway):
    """Mock Vector Store (개발용)"""

    def __init__(self, **kwargs):
        self.storage = {}

    @property
    def provider_name(self) -> str:
        return "mock"

    async def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """메모리에 저장"""
        for i, id_ in enumerate(ids):
            self.storage[id_] = {
                "vector": vectors[i],
                "metadata": metadata[i] if metadata else {},
            }
        return True

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """단순 반환 (실제 유사도 계산 없음)"""
        results = []
        for id_, data in list(self.storage.items())[:top_k]:
            results.append({
                "id": id_,
                "score": 0.9,  # Mock score
                "metadata": data["metadata"],
            })
        return results

    async def delete(self, ids: List[str]) -> bool:
        """삭제"""
        for id_ in ids:
            self.storage.pop(id_, None)
        return True


def get_vector_store_gateway(
    provider: Optional[str] = None,
    **kwargs
) -> VectorStoreGateway:
    """
    Vector Store Gateway Factory

    환경 변수:
        VECTOR_STORE_PROVIDER: mock | pinecone | weaviate | chroma (기본: mock)

    Args:
        provider: Provider 이름
        **kwargs: 추가 설정

    Returns:
        VectorStoreGateway: 선택된 Provider
    """
    provider = provider or os.getenv("VECTOR_STORE_PROVIDER", "mock")
    provider = provider.lower()

    if provider == "mock":
        return MockVectorStoreProvider(**kwargs)

    # TODO: 실제 Provider 구현
    # elif provider == "pinecone":
    #     return PineconeProvider(**kwargs)

    else:
        raise ValueError(f"Unknown vector store provider: {provider}")
