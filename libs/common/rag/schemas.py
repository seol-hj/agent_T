"""
RAG Schemas

RAG 관련 데이터 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Document(BaseModel):
    """문서 메타데이터"""

    document_id: str = Field(..., description="문서 고유 ID")
    title: str = Field(..., description="문서 제목")
    content: str = Field(..., description="문서 전체 내용")
    source: str = Field(..., description="문서 출처 (파일명, URL 등)")
    category: Optional[str] = Field(None, description="문서 카테고리 (정책, 사례연구, 기술문서 등)")
    tags: List[str] = Field(default_factory=list, description="문서 태그")
    metadata: dict = Field(default_factory=dict, description="추가 메타데이터")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="생성 일시")
    updated_at: Optional[str] = Field(None, description="수정 일시")


class Chunk(BaseModel):
    """문서 청크 (임베딩 단위)"""

    chunk_id: str = Field(..., description="청크 고유 ID")
    document_id: str = Field(..., description="원본 문서 ID")
    content: str = Field(..., description="청크 내용")
    start_index: int = Field(..., description="원본 문서에서의 시작 위치")
    end_index: int = Field(..., description="원본 문서에서의 종료 위치")
    embedding: Optional[List[float]] = Field(None, description="벡터 임베딩 (향후)")
    metadata: dict = Field(default_factory=dict, description="청크 메타데이터")


class RAGContext(BaseModel):
    """RAG 검색 컨텍스트"""

    document_id: str = Field(..., description="문서 ID")
    chunk_id: Optional[str] = Field(None, description="청크 ID (있는 경우)")
    content: str = Field(..., description="컨텍스트 내용")
    source: str = Field(..., description="출처")
    relevance_score: float = Field(..., description="관련도 점수 (0.0 ~ 1.0)")
    metadata: dict = Field(default_factory=dict, description="메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-001",
                "chunk_id": "chunk-001-1",
                "content": "교통 수요 증가 시나리오에서는...",
                "source": "traffic-policy-guide.pdf",
                "relevance_score": 0.85,
                "metadata": {"category": "정책", "page": 15}
            }
        }
