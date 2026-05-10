"""
In-Memory Retriever

메모리 기반 RAG 검색 (초기 구현용)
"""

from typing import List, Optional, Dict
import re

from .retriever import Retriever
from ..schemas import RAGContext, Document, Chunk


class InMemoryRetriever(Retriever):
    """
    메모리 기반 Retriever

    간단한 키워드 매칭으로 컨텍스트 검색
    초기 개발 및 테스트용
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 오버랩 (문자 수)
        """
        self.documents: Dict[str, Document] = {}
        self.chunks: Dict[str, List[Chunk]] = {}  # document_id -> chunks
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> List[RAGContext]:
        """키워드 기반 컨텍스트 검색"""

        # 쿼리 키워드 추출
        query_keywords = self._extract_keywords(query)

        # 모든 청크에서 검색
        results = []

        for document_id, chunks in self.chunks.items():
            document = self.documents.get(document_id)
            if not document:
                continue

            # 필터 적용
            if filters:
                if not self._apply_filters(document, filters):
                    continue

            for chunk in chunks:
                # 관련도 계산 (키워드 매칭)
                score = self._calculate_relevance(chunk.content, query_keywords)

                if score > 0:
                    context = RAGContext(
                        document_id=document_id,
                        chunk_id=chunk.chunk_id,
                        content=chunk.content,
                        source=document.source,
                        relevance_score=score,
                        metadata={
                            "title": document.title,
                            "category": document.category,
                            "tags": document.tags,
                        }
                    )
                    results.append(context)

        # 관련도 순으로 정렬 후 top_k 반환
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]

    async def add_document(self, document: Document) -> None:
        """문서 추가 및 청킹"""

        self.documents[document.document_id] = document

        # 문서를 청크로 분할
        chunks = self._chunk_document(document)
        self.chunks[document.document_id] = chunks

    async def remove_document(self, document_id: str) -> None:
        """문서 삭제"""

        if document_id in self.documents:
            del self.documents[document_id]

        if document_id in self.chunks:
            del self.chunks[document_id]

    async def get_document(self, document_id: str) -> Optional[Document]:
        """문서 조회"""
        return self.documents.get(document_id)

    async def list_documents(self) -> List[Document]:
        """모든 문서 목록"""
        return list(self.documents.values())

    def _chunk_document(self, document: Document) -> List[Chunk]:
        """문서를 청크로 분할"""

        content = document.content
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(content):
            end = min(start + self.chunk_size, len(content))

            chunk_content = content[start:end]

            chunk = Chunk(
                chunk_id=f"{document.document_id}-{chunk_index}",
                document_id=document.document_id,
                content=chunk_content,
                start_index=start,
                end_index=end,
                metadata={
                    "chunk_index": chunk_index,
                    "document_title": document.title,
                }
            )

            chunks.append(chunk)
            chunk_index += 1

            # 다음 청크 시작 위치 (오버랩 적용)
            start = end - self.chunk_overlap

        return chunks

    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""

        # 소문자 변환 및 특수문자 제거
        text = text.lower()
        text = re.sub(r'[^\w\s가-힣]', ' ', text)

        # 공백으로 분리
        words = text.split()

        # 중복 제거
        keywords = list(set(words))

        return keywords

    def _calculate_relevance(self, content: str, query_keywords: List[str]) -> float:
        """관련도 계산 (키워드 매칭)"""

        if not query_keywords:
            return 0.0

        content_lower = content.lower()

        # 매칭된 키워드 수
        matched = sum(1 for kw in query_keywords if kw in content_lower)

        # 관련도 = 매칭 비율
        score = matched / len(query_keywords)

        return score

    def _apply_filters(self, document: Document, filters: dict) -> bool:
        """필터 적용"""

        # 카테고리 필터
        if "category" in filters:
            if document.category != filters["category"]:
                return False

        # 태그 필터
        if "tags" in filters:
            required_tags = filters["tags"]
            if not all(tag in document.tags for tag in required_tags):
                return False

        return True
