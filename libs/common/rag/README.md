# RAG (Retrieval-Augmented Generation)

RAG 지원 모듈. 외부 문서에서 관련 컨텍스트를 검색하여 LLM 응답 품질을 향상시킨다.

## 개요

- **Document**: 원본 문서 메타데이터
- **Chunk**: 임베딩 단위로 분할된 문서 청크
- **RAGContext**: 검색된 컨텍스트
- **Retriever**: 컨텍스트 검색 인터페이스
- **DocumentLoader**: 문서 로드 (S3, 로컬)

## 구조

```
rag/
├── schemas.py                      # Document, Chunk, RAGContext
├── retrievers/
│   ├── retriever.py                # Retriever 인터페이스
│   ├── in_memory_retriever.py      # 메모리 기반 (초기 구현)
│   ├── vector_retriever.py         # 벡터 DB (placeholder)
│   ├── graph_retriever.py          # 그래프 DB (placeholder)
│   └── bedrock_kb_retriever.py     # Bedrock Knowledge Base (placeholder)
├── document_loader.py              # 문서 로더 (placeholder)
├── tests/
│   └── test_in_memory_retriever.py
└── README.md
```

## 주요 컴포넌트

### 1. Document

원본 문서 메타데이터.

```python
class Document(BaseModel):
    document_id: str
    title: str
    content: str
    source: str
    category: Optional[str]
    tags: List[str]
    metadata: dict
    created_at: str
    updated_at: Optional[str]
```

### 2. Chunk

문서를 임베딩 단위로 분할한 청크.

```python
class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    start_index: int
    end_index: int
    embedding: Optional[List[float]]  # 향후
    metadata: dict
```

### 3. RAGContext

검색된 컨텍스트.

```python
class RAGContext(BaseModel):
    document_id: str
    chunk_id: Optional[str]
    content: str
    source: str
    relevance_score: float  # 0.0 ~ 1.0
    metadata: dict
```

### 4. Retriever (인터페이스)

모든 Retriever가 구현해야 할 인터페이스.

```python
class Retriever(ABC):
    @abstractmethod
    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> List[RAGContext]:
        pass

    @abstractmethod
    async def add_document(self, document: Document) -> None:
        pass

    @abstractmethod
    async def remove_document(self, document_id: str) -> None:
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        pass

    @abstractmethod
    async def list_documents(self) -> List[Document]:
        pass
```

### 5. InMemoryRetriever

메모리 기반 RAG 검색 (초기 구현).

**특징**:
- 간단한 키워드 매칭
- 외부 의존성 없음
- 빠른 프로토타이핑
- 청킹 자동 지원

**키워드 매칭**:
1. 쿼리에서 키워드 추출
2. 청크 내용에서 키워드 매칭
3. 매칭 비율로 관련도 계산
4. 관련도 순 정렬

**청킹**:
- `chunk_size`: 청크 크기 (문자 수, 기본 500)
- `chunk_overlap`: 청크 오버랩 (문자 수, 기본 50)

**사용 예시**:
```python
from common.rag import InMemoryRetriever, Document

# Retriever 생성
retriever = InMemoryRetriever(chunk_size=500, chunk_overlap=50)

# 문서 추가
doc = Document(
    document_id="doc-001",
    title="교통 정책 가이드",
    content="교통 수요가 증가하면...",
    source="guide.pdf",
    category="정책",
    tags=["교통", "정책"],
)
await retriever.add_document(doc)

# 컨텍스트 검색
contexts = await retriever.retrieve_context("교통 수요 증가", top_k=5)

for ctx in contexts:
    print(f"[{ctx.relevance_score:.2f}] {ctx.content[:100]}...")
```

### 6. VectorRetriever (Placeholder)

벡터 DB 기반 RAG 검색 (향후 구현).

**계획**:
- OpenSearch Vector 검색
- Qdrant 통합
- 임베딩 모델 (Bedrock Titan Embeddings)
- 코사인 유사도 기반 검색

### 7. GraphRetriever (Placeholder)

그래프 DB 기반 RAG 검색 (향후 구현).

**계획**:
- Neo4j 통합
- 문서 간 관계 그래프
- 엔티티 추출 및 연결
- 그래프 쿼리 기반 검색

### 8. BedrockKnowledgeBaseRetriever (Placeholder)

AWS Bedrock Knowledge Base 기반 RAG 검색 (향후 구현).

**계획**:
- Bedrock Knowledge Base API 통합
- S3 데이터 소스 연동
- 자동 임베딩 및 검색
- RetrieveAndGenerate API 활용

### 9. DocumentLoader (Placeholder)

S3에서 문서 로드 (향후 구현).

**계획**:
- S3 rag-source 버킷에서 읽기
- PDF, DOCX, TXT, Markdown 파싱
- 메타데이터 추출
- 자동 청킹

## 사용법

### 기본 사용

```python
from common import get_rag_retriever
from common.rag import Document

# Retriever 가져오기 (환경 변수로 선택)
retriever = get_rag_retriever()

# 문서 추가
doc = Document(
    document_id="doc-001",
    title="제목",
    content="내용...",
    source="출처",
)
await retriever.add_document(doc)

# 검색
contexts = await retriever.retrieve_context("쿼리", top_k=5)
```

### 필터 적용

```python
# 카테고리 필터
contexts = await retriever.retrieve_context(
    "쿼리",
    top_k=5,
    filters={"category": "정책"}
)

# 태그 필터
contexts = await retriever.retrieve_context(
    "쿼리",
    top_k=5,
    filters={"tags": ["교통", "시뮬레이션"]}
)
```

### Orchestrator에서 사용

```python
from common import get_rag_retriever

retriever = get_rag_retriever()

# 컨텍스트 검색
rag_contexts = await retriever.retrieve_context(user_input, top_k=3)

# LLM에 주입
response = await llm.generate(
    prompt=build_prompt(user_input, rag_contexts),
)
```

### Reporter에서 사용

```python
# 분석 결과 관련 참고 자료 검색
rag_contexts = await retriever.retrieve_context(
    f"교통 {request_type} 정책 사례",
    top_k=5
)

# 리포트에 포함
report = await reporter.generate_report(
    analysis_result=analysis_result,
    rag_contexts=rag_contexts,
)
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `RAG_RETRIEVER` | `in_memory` | Retriever 타입 (`in_memory` / `vector` / `bedrock_kb`) |
| `RAG_CHUNK_SIZE` | `500` | 청크 크기 (문자 수) |
| `RAG_CHUNK_OVERLAP` | `50` | 청크 오버랩 (문자 수) |

## 테스트

```bash
# RAG 테스트 실행
pytest libs/common/rag/tests/ -v

# InMemoryRetriever 테스트
pytest libs/common/rag/tests/test_in_memory_retriever.py -v
```

**테스트 케이스** (12개):
- 문서 추가/삭제/조회
- 문서 목록
- 기본 검색
- 필터 적용 검색
- top_k 제한
- 청킹
- 관련도 순 정렬
- 검색 결과 없음
- 메타데이터 포함

## 확장 계획

### VectorRetriever 구현

1. **OpenSearch 통합**:
   ```python
   retriever = VectorRetriever(
       vector_db_type="opensearch",
       endpoint="https://opensearch-endpoint",
       embedding_model="bedrock-titan-embeddings"
   )
   ```

2. **임베딩 생성**:
   - Bedrock Titan Embeddings
   - 1536 차원 벡터

3. **검색**:
   - 코사인 유사도
   - 하이브리드 검색 (키워드 + 벡터)

### GraphRetriever 구현

1. **Neo4j 통합**:
   ```python
   retriever = GraphRetriever(
       graph_db_uri="bolt://localhost:7687",
       username="neo4j",
       password="password"
   )
   ```

2. **엔티티 추출**:
   - 교통 정책, 지역, 도로명 등
   - 엔티티 간 관계 정의

3. **그래프 쿼리**:
   - Cypher 쿼리
   - 관련 문서 탐색

### BedrockKnowledgeBaseRetriever 구현

1. **Knowledge Base 설정**:
   - S3 데이터 소스 연결
   - 자동 임베딩 및 인덱싱

2. **Retrieve API**:
   ```python
   retriever = BedrockKnowledgeBaseRetriever(
       knowledge_base_id="kb-123456",
       region="us-east-1"
   )
   ```

3. **RetrieveAndGenerate**:
   - 검색 + 생성 통합

### DocumentLoader 구현

1. **S3 통합**:
   ```python
   loader = DocumentLoader(s3_bucket="agent-t-rag-source")
   documents = await loader.load_from_s3(prefix="policies/")
   ```

2. **파일 파싱**:
   - PDF: PyPDF2, pdfplumber
   - DOCX: python-docx
   - Markdown: python-markdown

3. **메타데이터 추출**:
   - 제목, 작성자, 날짜
   - 자동 태그 생성

## 제약 사항

- **초기 구현**: InMemoryRetriever만 사용 가능
- **키워드 매칭**: 단순 매칭, 시맨틱 검색 미지원
- **청킹**: 고정 크기, 문장/문단 단위 분할 미지원
- **임베딩**: 벡터 임베딩 미지원

## 다음 단계

1. **VectorRetriever 구현**: OpenSearch/Qdrant 통합
2. **임베딩 모델**: Bedrock Titan Embeddings
3. **DocumentLoader 구현**: S3 + PDF 파싱
4. **하이브리드 검색**: 키워드 + 벡터 결합
5. **재순위화**: LLM 기반 reranking
6. **자동 업데이트**: S3 이벤트 트리거로 자동 인덱싱

## 참고

- [AWS Bedrock Knowledge Base](https://aws.amazon.com/bedrock/knowledge-bases/)
- [OpenSearch Vector Search](https://opensearch.org/docs/latest/search-plugins/knn/)
- [Qdrant](https://qdrant.tech/)
- [Neo4j](https://neo4j.com/)
