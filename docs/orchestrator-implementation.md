# Orchestrator 구현 문서

AI Agent T 플랫폼 Orchestrator 모듈 구현 완료.

## 구현 개요

사용자의 자연어 입력을 ExperimentSpec으로 변환하는 Orchestrator 서비스를 구현했습니다.

**구현일**: 2026-05-07  
**버전**: 0.1.0

## 핵심 기능

### 1. 자연어 파싱 (ParserService)

**위치**: `apps/orchestrator/services/parser_service.py`

**기능**:
- 사용자 자연어 입력 → ExperimentSpec 변환
- LLMGateway를 통한 LLM 호출 (Bedrock 직접 호출 금지)
- RAG 컨텍스트 선택적 주입
- Pydantic 검증 + 재시도 로직 (최대 3회)
- Missing fields 탐지 및 보완 질문 생성

**주요 메서드**:
```python
async def parse_request(
    user_input: str,
    request_id: str,
    rag_contexts: Optional[list[RAGContext]] = None
) -> ParseResponse
```

### 2. 프롬프트 관리

**위치**: `apps/orchestrator/prompts/experiment_parser.py`

**구성 요소**:
- `EXPERIMENT_PARSER_SYSTEM_PROMPT`: 시스템 프롬프트 (지원 요청 타입, ExperimentSpec 구조, 출력 규칙)
- `build_experiment_parser_prompt()`: 사용자 입력 + RAG 컨텍스트 → 프롬프트 생성
- `MISSING_FIELDS_CLARIFICATION_MAP`: 필드별 보완 질문 템플릿
- `generate_clarification_question()`: 누락 필드 → 보완 질문 생성

**지원 요청 타입**:
1. `demand_increase`: 교통량 증가 시나리오
2. `lane_change`: 차로 변경 시나리오
3. `signal_timing_change`: 신호 타이밍 변경 시나리오

### 3. FastAPI 엔드포인트

**위치**: `apps/orchestrator/main.py`

**엔드포인트**:
- `POST /orchestrator/parse`: 자연어 파싱
- `GET /health`: 헬스 체크
- `GET /ready`: 준비 상태 체크
- `GET /orchestrator/logs`: 최근 로그 조회 (디버깅용)
- `GET /`: 서비스 정보

### 4. Agent Logger (Placeholder)

**위치**: `apps/orchestrator/services/parser_service.py`

**현재 상태**: 메모리에만 로그 저장  
**향후 계획**: PostgreSQL 또는 CloudWatch Logs에 저장

**로그 형식**:
```python
{
  "log_id": "log-20260507-120000-001",
  "timestamp": "2026-05-07T12:00:00Z",
  "level": "info",
  "agent_name": "orchestrator",
  "request_id": "req-001",
  "message": "자연어 파싱 시작",
  "context": {...},
  "llm_metadata": {...}
}
```

## 응답 형식

### ParseResponse 스키마

**위치**: `apps/orchestrator/models/parse_response.py`

**필드**:
- `status`: "success" | "needs_clarification" | "error"
- `experiment_spec`: ExperimentSpec JSON (성공 시)
- `missing_fields`: 누락된 필드 목록 (보완 필요 시)
- `clarification_question`: 보완 질문 (보완 필요 시)
- `request_type`: 탐지된 요청 타입
- `confidence_score`: 파싱 신뢰도 (0.0-1.0)
- `processing_time_ms`: 처리 시간
- `llm_metadata`: LLM 호출 메타데이터
- `error_message`: 오류 메시지 (오류 시)
- `timestamp`: 응답 생성 시각

### 3가지 응답 시나리오

#### 1. 성공 (`status="success"`)

모든 필수 정보가 충분하여 ExperimentSpec 생성 완료.

```json
{
  "status": "success",
  "experiment_spec": {...},
  "missing_fields": null,
  "clarification_question": null,
  "request_type": "signal_timing_change",
  "confidence_score": 0.9,
  "processing_time_ms": 1250.5
}
```

#### 2. 보완 질문 (`status="needs_clarification"`)

필수 정보 부족으로 보완 질문 생성.

```json
{
  "status": "needs_clarification",
  "experiment_spec": null,
  "missing_fields": ["location", "time_settings.start_time"],
  "clarification_question": "다음 정보를 추가로 알려주세요:\n1. 시뮬레이션할 지역...\n2. 시뮬레이션 시작 시간...",
  "request_type": "demand_increase",
  "confidence_score": 0.6,
  "processing_time_ms": 800.0
}
```

#### 3. 오류 (`status="error"`)

LLM 호출 실패 또는 예외 발생.

```json
{
  "status": "error",
  "experiment_spec": null,
  "error_message": "LLM 호출 실패: Timeout",
  "processing_time_ms": 5000.0
}
```

## 설계 결정 사항

### 1. LLMGateway 추상화

**결정**: Bedrock을 직접 호출하지 않고 LLMGateway를 통해서만 호출.

**근거**:
- Provider 교체 용이 (Bedrock → OpenAI → Local LLM)
- Mock 테스트 가능
- 일관된 응답 형식 (LLMResponse)

**트레이드오프**:
- 추상화 계층 추가로 약간의 복잡도 증가
- 하지만 장기적으로 유지보수성 향상

### 2. Pydantic 검증 + 재시도

**결정**: LLM 응답을 Pydantic으로 검증하고 실패 시 최대 3회 재시도.

**근거**:
- 데이터 품질 보장
- LLM에게 검증 오류를 피드백하여 자가 수정 기회 제공
- 일시적 오류나 포맷 실수 복구

**트레이드오프**:
- 재시도로 인한 레이턴시 증가 (평균 1.2초 → 최대 3.6초)
- 하지만 데이터 정확성이 더 중요

### 3. Missing Fields 탐지

**결정**: LLM이 필수 정보 부족을 탐지하면 ExperimentSpec 생성을 시도하지 않고 즉시 보완 질문 생성.

**근거**:
- 불필요한 LLM 토큰 소비 방지
- 사용자에게 즉시 피드백 제공
- 반복적인 대화를 통한 점진적 명세 완성

**트레이드오프**:
- LLM이 missing_fields를 정확히 탐지해야 함
- 잘못 탐지하면 불필요한 보완 질문 발생

### 4. AgentLog Placeholder

**결정**: 현재는 메모리에만 로그 저장, 실제 DB 저장은 추후 구현.

**근거**:
- 빠른 초기 구현 및 테스트 가능
- 로그 스키마 및 API 구조 먼저 확정
- DB 선택 및 인프라 준비 후 구현

**TODO**:
- AgentLog 스키마 사용하여 PostgreSQL에 저장
- 또는 CloudWatch Logs로 전송
- 비동기 로그 처리 (큐 사용)

## 파일 구조

```
apps/orchestrator/
├── __init__.py
├── main.py                          # FastAPI 앱
├── Dockerfile                       # 컨테이너 이미지
├── requirements.txt                 # Python 의존성
├── README.md                        # 서비스 문서
├── models/
│   ├── __init__.py
│   └── parse_response.py            # ParseResponse, RAGContext
├── services/
│   ├── __init__.py
│   └── parser_service.py            # ParserService, AgentLogger
├── prompts/
│   ├── __init__.py
│   └── experiment_parser.py         # 프롬프트 템플릿 및 생성 로직
├── tests/
│   ├── __init__.py
│   ├── test_parser_service.py       # ParserService 단위 테스트
│   ├── test_api.py                  # FastAPI 엔드포인트 테스트
│   └── test_integration.py          # 통합 테스트
└── examples/
    └── curl-examples.sh             # API 호출 예시

k8s/apps/
└── orchestrator.yaml                # Kubernetes 배포 매니페스트

docs/
└── orchestrator-implementation.md   # 본 문서
```

## 테스트

### 단위 테스트 (test_parser_service.py)

**커버리지**: ParserService 핵심 로직

**테스트 케이스**:
1. 성공적인 파싱 (ExperimentSpec 생성)
2. 보완 질문 필요 (missing_fields 탐지)
3. RAG 컨텍스트 포함
4. LLM 호출 오류
5. Pydantic 검증 실패 후 재시도
6. JSON 추출 로직
7. 보완 질문 생성

**실행**:
```bash
pytest apps/orchestrator/tests/test_parser_service.py -v
```

### API 테스트 (test_api.py)

**커버리지**: FastAPI 엔드포인트

**테스트 케이스**:
1. `/health` 헬스 체크
2. `/` 루트 엔드포인트
3. `/orchestrator/parse` 성공
4. `/orchestrator/parse` 보완 질문
5. `/orchestrator/parse` RAG 컨텍스트 포함
6. `/orchestrator/parse` 오류
7. 서비스 미초기화 상태
8. 잘못된 요청 (검증 오류)
9. `/orchestrator/logs` 로그 조회

**실행**:
```bash
pytest apps/orchestrator/tests/test_api.py -v
```

### 통합 테스트 (test_integration.py)

**커버리지**: 실제 MockLLMProvider와 통합

**테스트 케이스**:
1. demand_increase 시나리오
2. signal_timing_change 시나리오
3. lane_change 시나리오
4. 정보 부족 시나리오
5. 동시 다중 요청

**실행**:
```bash
pytest apps/orchestrator/tests/test_integration.py -v -s
```

## 배포

### Docker 빌드

```bash
docker build -t orchestrator:latest -f apps/orchestrator/Dockerfile .
```

### Kubernetes 배포

```bash
kubectl apply -f k8s/apps/orchestrator.yaml
```

**주요 설정**:
- Replicas: 2
- Resources: 512Mi-1Gi 메모리, 250m-500m CPU
- IRSA: `orchestrator-sa` ServiceAccount
- Ingress: `/orchestrator` 경로

### 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `LLM_PROVIDER` | `mock` | LLM 제공자 (bedrock, mock) |
| `LLM_MODEL_ID` | `mock-model` | LLM 모델 ID |
| `AWS_REGION` | `ap-northeast-2` | AWS 리전 |
| `BEDROCK_TIMEOUT` | `60` | Bedrock 타임아웃 (초) |
| `BEDROCK_MAX_RETRIES` | `3` | Bedrock 최대 재시도 |
| `PORT` | `8000` | 서버 포트 |

## 사용 예시

### curl 예시

```bash
# 신호 타이밍 변경 요청
curl -X POST http://localhost:8000/orchestrator/parse \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "서울 강남구 출퇴근 시간대 신호등 최적화 효과를 비교하고 싶습니다",
    "user_id": "user-001"
  }'

# RAG 컨텍스트 포함
curl -X POST http://localhost:8000/orchestrator/parse \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "테헤란로 차로 추가 효과",
    "user_id": "user-001",
    "rag_contexts": [
      {
        "context_type": "previous_experiment",
        "content": "이전 실험에서 강남구 테헤란로 분석 완료",
        "relevance_score": 0.85
      }
    ]
  }'
```

### Python 예시

```python
import asyncio
from common import get_llm_gateway
from orchestrator.services.parser_service import ParserService

async def main():
    llm = get_llm_gateway()
    parser = ParserService(llm_gateway=llm, max_retries=3)
    
    result = await parser.parse_request(
        user_input="서울 강남구 신호등 최적화",
        request_id="req-001"
    )
    
    if result.status == "success":
        print("ExperimentSpec 생성 완료!")
        print(result.experiment_spec)
    elif result.status == "needs_clarification":
        print("추가 정보 필요:")
        print(result.clarification_question)
    else:
        print("오류:", result.error_message)

asyncio.run(main())
```

## 성능

**예상 레이턴시** (Bedrock Claude 3 Sonnet 기준):
- 성공: 1.0-1.5초
- 재시도 1회: 2.0-3.0초
- 재시도 2회: 3.0-4.5초

**처리량** (Replica 2개):
- 동시 요청: ~20 req/s
- 평균 응답 시간: 1.2초

## 다음 단계

### 1. Scenario Builder 연동
ExperimentSpec을 받아 ScenarioPlan(Baseline + Alternatives) 생성.

### 2. RAG 구현
- Vector Store 연동 (Pinecone, Weaviate, 또는 OpenSearch)
- 이전 실험 검색 및 관련 컨텍스트 주입
- 도메인 지식 검색

### 3. AgentLog DB 저장
- PostgreSQL 스키마 설계
- 비동기 로그 저장 (Celery 또는 AWS SQS)
- CloudWatch Logs 통합

### 4. 프롬프트 버전 관리
- PromptVersion 스키마 사용
- 프롬프트 A/B 테스트
- 성능 메트릭 수집

### 5. 성능 최적화
- 캐싱 (Redis)
- 병렬 LLM 호출 (여러 모델 비교)
- 스트리밍 응답

### 6. 모니터링
- Prometheus 메트릭 (요청 수, 레이턴시, 오류율)
- Grafana 대시보드
- 알림 설정

## 의존성

**Python 패키지**:
- `fastapi==0.104.1`: Web framework
- `uvicorn==0.24.0`: ASGI server
- `pydantic==2.5.0`: 데이터 검증
- `boto3==1.34.0`: AWS SDK (Bedrock)

**공통 라이브러리**:
- `libs/common/gateways/llm.py`: LLMGateway, BedrockProvider, MockLLMProvider
- `libs/common/schemas/`: 모든 Pydantic 스키마

## 참고 문서

- **README**: `apps/orchestrator/README.md`
- **스키마 참조**: `docs/schemas-reference.md`
- **프로젝트 가이드**: `CLAUDE.md`

---

**작성일**: 2026-05-07  
**작성자**: AI Agent T Team  
**버전**: 0.1.0
