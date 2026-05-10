"""
In-Memory Retriever Tests

InMemoryRetriever 단위 테스트
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.rag import InMemoryRetriever, Document


@pytest.fixture
def retriever():
    """InMemoryRetriever 인스턴스"""
    return InMemoryRetriever(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def sample_documents():
    """샘플 문서"""
    return [
        Document(
            document_id="doc-001",
            title="교통 수요 증가 시나리오",
            content="교통 수요가 20% 증가했을 때, 평균 통행 시간이 증가하고 대기 시간도 늘어납니다. 차선 추가나 신호 타이밍 조정이 필요합니다.",
            source="traffic-scenario-guide.pdf",
            category="정책",
            tags=["교통수요", "시나리오"],
        ),
        Document(
            document_id="doc-002",
            title="차선 변경 효과",
            content="차선을 1개 추가하면 교통 용량이 증가하여 혼잡도가 감소합니다. 그러나 비용이 많이 들고 공사 기간이 필요합니다.",
            source="lane-change-study.pdf",
            category="사례연구",
            tags=["차선변경", "효과분석"],
        ),
        Document(
            document_id="doc-003",
            title="신호 타이밍 최적화",
            content="신호 타이밍을 최적화하면 대기 시간을 줄일 수 있습니다. 첨두 시간대에는 녹색 시간을 늘리는 것이 효과적입니다.",
            source="signal-timing-best-practices.pdf",
            category="기술문서",
            tags=["신호타이밍", "최적화"],
        ),
    ]


@pytest.mark.asyncio
async def test_add_document(retriever, sample_documents):
    """문서 추가 테스트"""
    doc = sample_documents[0]
    await retriever.add_document(doc)

    # 문서가 추가되었는지 확인
    retrieved = await retriever.get_document(doc.document_id)
    assert retrieved is not None
    assert retrieved.document_id == doc.document_id
    assert retrieved.title == doc.title


@pytest.mark.asyncio
async def test_list_documents(retriever, sample_documents):
    """문서 목록 조회 테스트"""
    for doc in sample_documents:
        await retriever.add_document(doc)

    documents = await retriever.list_documents()
    assert len(documents) == 3


@pytest.mark.asyncio
async def test_remove_document(retriever, sample_documents):
    """문서 삭제 테스트"""
    doc = sample_documents[0]
    await retriever.add_document(doc)

    # 삭제
    await retriever.remove_document(doc.document_id)

    # 삭제되었는지 확인
    retrieved = await retriever.get_document(doc.document_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_retrieve_context_basic(retriever, sample_documents):
    """기본 컨텍스트 검색 테스트"""
    for doc in sample_documents:
        await retriever.add_document(doc)

    # "교통 수요" 검색
    contexts = await retriever.retrieve_context("교통 수요 증가", top_k=3)

    assert len(contexts) > 0
    assert contexts[0].relevance_score > 0

    # 가장 관련도 높은 컨텍스트가 doc-001에서 나온 것인지 확인
    assert contexts[0].document_id == "doc-001"


@pytest.mark.asyncio
async def test_retrieve_context_with_filter(retriever, sample_documents):
    """필터 적용 검색 테스트"""
    for doc in sample_documents:
        await retriever.add_document(doc)

    # 카테고리 필터
    contexts = await retriever.retrieve_context(
        "차선",
        top_k=5,
        filters={"category": "사례연구"}
    )

    # 사례연구 카테고리 문서만 반환
    assert len(contexts) > 0
    for ctx in contexts:
        assert ctx.metadata["category"] == "사례연구"


@pytest.mark.asyncio
async def test_retrieve_context_top_k(retriever, sample_documents):
    """top_k 제한 테스트"""
    for doc in sample_documents:
        await retriever.add_document(doc)

    contexts = await retriever.retrieve_context("교통", top_k=2)

    assert len(contexts) <= 2


@pytest.mark.asyncio
async def test_chunking(retriever):
    """청킹 테스트"""
    long_content = "가" * 250  # 100자 청크, 20자 오버랩이므로 3개 청크 예상

    doc = Document(
        document_id="doc-long",
        title="긴 문서",
        content=long_content,
        source="test",
    )

    await retriever.add_document(doc)

    # 청크가 생성되었는지 확인
    chunks = retriever.chunks.get(doc.document_id, [])
    assert len(chunks) > 1


@pytest.mark.asyncio
async def test_relevance_score_order(retriever, sample_documents):
    """관련도 순 정렬 테스트"""
    for doc in sample_documents:
        await retriever.add_document(doc)

    contexts = await retriever.retrieve_context("차선 추가", top_k=5)

    # 관련도가 내림차순으로 정렬되어 있는지 확인
    for i in range(len(contexts) - 1):
        assert contexts[i].relevance_score >= contexts[i + 1].relevance_score


@pytest.mark.asyncio
async def test_no_results(retriever, sample_documents):
    """검색 결과 없음 테스트"""
    for doc in sample_documents:
        await retriever.add_document(doc)

    contexts = await retriever.retrieve_context("완전히 관계없는 키워드", top_k=5)

    # 관련도가 0인 경우 결과 없음
    assert len(contexts) == 0


@pytest.mark.asyncio
async def test_metadata_included(retriever, sample_documents):
    """메타데이터 포함 확인"""
    doc = sample_documents[0]
    await retriever.add_document(doc)

    contexts = await retriever.retrieve_context("교통", top_k=1)

    assert len(contexts) > 0
    ctx = contexts[0]
    assert "title" in ctx.metadata
    assert "category" in ctx.metadata
    assert "tags" in ctx.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
