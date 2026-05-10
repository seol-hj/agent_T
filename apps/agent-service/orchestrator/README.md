# Orchestrator Service

AI Agent T 플랫폼의 오케스트레이터 서비스.

## 역할

- 사용자 자연어 입력 해석
- RAG 컨텍스트 선택적 주입
- ExperimentSpec 생성
- 누락된 필드 탐지 및 보완 질문 생성
- Scenario Builder 호출 준비

## 핵심 기능

### 1. 자연어 → ExperimentSpec 변환

사용자의 자연어 요청을 구조화된 실험 명세로 변환합니다.

**지원하는 요청 타입**:
- `demand_increase`: 교통량 증가 시나리오
- `lane_change`: 차로 변경 시나리오
- `signal_timing_change`: 신호 타이밍 변경 시나리오

### 2. Missing Fields 탐지

필수 정보가 부족한 경우 자동으로 탐지하고 보완 질문을 생성합니다.

### 3. RAG 컨텍스트 주입

이전 실험 정보나 도메인 지식을 참고하여 더 정확한 해석을 수행합니다.

### 4. Pydantic 검증 + 재시도

생성된 ExperimentSpec이 Pydantic 검증을 통과할 때까지 최대 3회 재시도합니다.

## 아키텍처

```
┌─────────────────────┐
│   FastAPI Main      │
│   (main.py)         │
└──────────┬──────────┘
           │
           ├─► ParserService (services/parser_service.py)
           │   ├─► LLMGateway (common/gateways/llm.py)
           │   │   └─► BedrockProvider / MockProvider
           │   ├─► Prompts (prompts/experiment_parser.py)
           │   └─► Pydantic Validation (common/schemas/experiment.py)
           │
           └─► AgentLogger (services/parser_service.py)
               └─► 로그 저장 (현재는 메모리, 향후 DB)
```

## 설치 및 실행

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
export LLM_PROVIDER=mock  # 또는 bedrock
export LLM_MODEL_ID=mock-model
export AWS_REGION=ap-northeast-2  # Bedrock 사용 시

# 서버 시작
python -m uvicorn apps.orchestrator.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t orchestrator:latest -f apps/orchestrator/Dockerfile .

# 컨테이너 실행
docker run -d \
  -p 8000:8000 \
  -e LLM_PROVIDER=mock \
  -e LLM_MODEL_ID=mock-model \
  orchestrator:latest
```

## API 엔드포인트

### 1. `/orchestrator/parse` (POST)

사용자 자연어 입력을 ExperimentSpec으로 변환합니다.

**요청**:
```json
{
  "user_input": "서울 강남구 출퇴근 시간대 교통량을 분석하고 신호등 최적화 효과를 비교하고 싶습니다",
  "user_id": "user-001",
  "rag_contexts": [  // Optional
    {
      "context_type": "previous_experiment",
      "content": "이전 실험에서 강남구를 분석했습니다.",
      "relevance_score": 0.8,
      "source": "exp-001"
    }
  ]
}
```

**응답 (성공)**:
```json
{
  "status": "success",
  "experiment_spec": {
    "experiment_id": "exp-20260507-001",
    "request_id": "req-20260507-120000",
    "title": "강남구 출퇴근 시간대 신호등 최적화 효과 분석",
    "description": "서울 강남구 출퇴근 시간대의 교통 혼잡을 완화하기 위한 신호등 최적화 방안 비교",
    "location": {
      "region": "서울특별시 강남구",
      "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
      "osm_query": "Gangnam-gu, Seoul, South Korea"
    },
    "time_settings": {
      "start_time": "07:00",
      "end_time": "09:00",
      "duration_hours": 2,
      "time_period": "weekday_morning_rush"
    },
    "traffic_settings": {
      "vehicle_count": 5000,
      "vehicle_types": ["passenger", "bus", "truck"],
      "vehicle_distribution": {"passenger": 0.8, "bus": 0.1, "truck": 0.1},
      "demand_level": "high"
    },
    "objectives": ["평균 통행 시간 20% 단축", "차량 배출량 15% 감소"],
    "constraints": ["기존 도로 인프라 유지"]
  },
  "missing_fields": null,
  "clarification_question": null,
  "request_type": "signal_timing_change",
  "confidence_score": 0.9,
  "processing_time_ms": 1250.5,
  "llm_metadata": {
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "provider": "bedrock",
    "prompt_version": "experiment-parser-v1.0",
    "latency_ms": 1200.0,
    "input_tokens": 1200,
    "output_tokens": 450
  },
  "timestamp": "2026-05-07T12:00:00.000Z"
}
```

**응답 (보완 질문 필요)**:
```json
{
  "status": "needs_clarification",
  "experiment_spec": null,
  "missing_fields": ["location", "time_settings.start_time"],
  "clarification_question": "다음 정보를 추가로 알려주세요:\n1. 시뮬레이션할 지역의 위치를 알려주세요. 예: 서울 강남구\n2. 시뮬레이션 시작 시간을 알려주세요. 예: 07:00",
  "request_type": "demand_increase",
  "confidence_score": 0.6,
  "processing_time_ms": 800.0,
  "llm_metadata": {...},
  "timestamp": "2026-05-07T12:00:00.000Z"
}
```

**응답 (오류)**:
```json
{
  "status": "error",
  "experiment_spec": null,
  "missing_fields": null,
  "clarification_question": null,
  "error_message": "LLM 호출 실패: Connection timeout",
  "processing_time_ms": 5000.0,
  "timestamp": "2026-05-07T12:00:00.000Z"
}
```

### 2. `/health` (GET)

헬스 체크 엔드포인트.

**응답**:
```json
{
  "status": "healthy",
  "service": "orchestrator",
  "timestamp": "2026-05-07T12:00:00.000Z",
  "version": "0.1.0"
}
```

### 3. `/ready` (GET)

준비 상태 체크 엔드포인트.

**응답**:
```json
{
  "status": "ready",
  "service": "orchestrator",
  "timestamp": "2026-05-07T12:00:00.000Z"
}
```

### 4. `/orchestrator/logs` (GET)

최근 로그 조회 (디버깅용).

**쿼리 파라미터**:
- `limit`: 조회할 로그 개수 (기본 50)

**응답**:
```json
{
  "logs": [
    {
      "log_id": "log-20260507-120000-001",
      "timestamp": "2026-05-07T12:00:00.000Z",
      "level": "info",
      "agent_name": "orchestrator",
      "request_id": "req-20260507-120000",
      "message": "자연어 파싱 시작",
      "context": {...}
    }
  ],
  "total": 15
}
```

## 프롬프트 관리

프롬프트는 `prompts/experiment_parser.py`에서 관리됩니다.

### 시스템 프롬프트

`EXPERIMENT_PARSER_SYSTEM_PROMPT`에 전역 지침이 정의되어 있습니다:
- 지원하는 요청 타입
- ExperimentSpec 구조
- 출력 규칙
- 지역별 bbox 참고값
- 출퇴근 시간대 참고값

### 프롬프트 빌드

`build_experiment_parser_prompt()` 함수가 사용자 입력과 RAG 컨텍스트를 조합하여 프롬프트를 생성합니다.

### 보완 질문 생성

`MISSING_FIELDS_CLARIFICATION_MAP`에 필드별 보완 질문이 정의되어 있습니다.

## 테스트

```bash
# 단위 테스트 실행
pytest apps/orchestrator/tests/test_parser_service.py -v

# API 테스트 실행
pytest apps/orchestrator/tests/test_api.py -v

# 전체 테스트 실행
pytest apps/orchestrator/tests/ -v
```

### 주요 테스트 케이스

- 성공적인 파싱 (ExperimentSpec 생성)
- 보완 질문 필요 (missing_fields 탐지)
- RAG 컨텍스트 포함
- LLM 호출 오류
- Pydantic 검증 실패 후 재시도
- API 엔드포인트 통합 테스트

## 설계 결정 사항

### 1. LLMGateway만 사용

Bedrock을 직접 호출하지 않고 `LLMGateway`를 통해서만 LLM을 호출합니다.
- **장점**: Provider 교체 용이, Mock 테스트 가능
- **단점**: 추상화 계층 추가

### 2. Pydantic 검증 + 재시도

LLM이 생성한 ExperimentSpec이 Pydantic 검증을 통과하지 못하면 오류 메시지를 피드백으로 제공하고 최대 3회 재시도합니다.
- **장점**: 데이터 품질 보장, LLM 자가 수정
- **단점**: 재시도로 인한 레이턴시 증가

### 3. Missing Fields 탐지

필수 정보가 부족하면 ExperimentSpec 생성을 시도하지 않고 즉시 보완 질문을 생성합니다.
- **장점**: 불필요한 LLM 호출 방지, 사용자 경험 개선
- **단점**: LLM이 missing_fields를 정확히 탐지해야 함

### 4. AgentLog Placeholder

현재는 메모리에만 로그를 저장하지만, 실제 구현에서는 PostgreSQL 또는 CloudWatch Logs에 저장해야 합니다.
- **TODO**: AgentLog 스키마 사용하여 DB 저장 구현

## 환경변수

| 변수 | 설명 | 기본값 | 예시 |
|------|------|--------|------|
| `LLM_PROVIDER` | LLM 제공자 | `mock` | `bedrock`, `mock` |
| `LLM_MODEL_ID` | LLM 모델 ID | `mock-model` | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `AWS_REGION` | AWS 리전 (Bedrock 사용 시) | `ap-northeast-2` | `us-east-1` |
| `BEDROCK_TIMEOUT` | Bedrock 타임아웃 (초) | `60` | `30` |
| `BEDROCK_MAX_RETRIES` | Bedrock 최대 재시도 | `3` | `5` |
| `PORT` | 서버 포트 | `8000` | `8000` |

## 다음 단계

1. **Scenario Builder 연동**: ExperimentSpec → ScenarioPlan 생성
2. **RAG 구현**: Vector Store에서 관련 컨텍스트 검색
3. **AgentLog DB 저장**: PostgreSQL 또는 CloudWatch Logs 연동
4. **프롬프트 버전 관리**: PromptVersion 스키마 사용
5. **성능 최적화**: 캐싱, 병렬 처리
6. **모니터링**: Prometheus 메트릭 추가

## 참고

- **공통 스키마**: `libs/common/schemas/`
- **LLM Gateway**: `libs/common/gateways/llm.py`
- **프롬프트**: `apps/orchestrator/prompts/experiment_parser.py`
