# Observability Architecture

AI Agent T 플랫폼의 관측성 아키텍처.

---

## 개요

AI Agent T는 **두 가지 관측성 계층**을 분리하여 운영:

1. **시스템 관측성** (Kubernetes Monitoring)
   - Prometheus + Grafana
   - 시스템 상태, 리소스 사용, 가용성
   - SRE/DevOps 팀이 사용

2. **AI 품질 관측성** (Structured Logging)
   - OpenTelemetry + CloudWatch Logs
   - LLM 호출, Pipeline 단계, 실험 결과
   - AI/ML 팀이 사용

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent T Services                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │Orchestrator│  │  Network   │  │  Simulator │            │
│  │            │  │  Builder   │  │   Runner   │  ...       │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │                │                │                    │
│        │ Structured     │ Structured     │ Structured        │
│        │ Logs (JSON)    │ Logs (JSON)    │ Logs (JSON)      │
│        └────────────────┴────────────────┘                   │
│                         │                                     │
│                         ▼                                     │
│              ┌──────────────────────┐                        │
│              │  Observability Lib   │                        │
│              │  - Context           │                        │
│              │  - Logger            │                        │
│              │  - Metrics           │                        │
│              │  - LLM Metrics       │                        │
│              │  - Pipeline Metrics  │                        │
│              └──────────┬───────────┘                        │
└─────────────────────────┼──────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────────┐           ┌──────────────────────┐
│ System Monitoring │           │  AI Quality Logs     │
│                   │           │                      │
│  Prometheus       │           │  CloudWatch Logs     │
│  └─ Metrics       │           │  └─ JSON Logs        │
│  Grafana          │           │  OpenSearch          │
│  └─ Dashboards    │           │  └─ Analysis         │
│                   │           │                      │
│  Focus:           │           │  Focus:              │
│  - CPU/Memory     │           │  - LLM Latency       │
│  - Pod Health     │           │  - Token Usage       │
│  - Request Rate   │           │  - Pipeline Steps    │
│  - Error Rate     │           │  - Experiment Data   │
└───────────────────┘           └──────────────────────┘
```

---

## 1. 시스템 관측성 (Kubernetes Monitoring)

### Prometheus + Grafana

**목적**: 시스템 상태 모니터링, 장애 감지, SLO 추적

**메트릭**:
- CPU/메모리 사용률 (Node, Pod)
- Request rate, Error rate, Duration (RED)
- Pod restart count
- Job 실행 상태

**설치**:
```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

**Grafana 대시보드**:
- Agent-T Overview (서비스별 상태)
- Pipeline Execution (파이프라인 실행 추이)
- Resource Usage (CPU/메모리)
- Error Tracking (에러율)

**자세한 내용**: [k8s/monitoring/INSTALL.md](../k8s/monitoring/INSTALL.md)

---

## 2. AI 품질 관측성 (Structured Logging)

### OpenTelemetry + CloudWatch Logs

**목적**: AI 품질 평가, LLM 비용 추적, 실험 분석

**로그 구조**:
- JSON 포맷 (파싱 용이)
- 컨텍스트 자동 포함 (request_id, experiment_id, run_id)
- 메타데이터 확장 가능

**수집 로그**:
1. **LLM 호출 메트릭**
   - Latency (ms)
   - Token 사용량 (prompt, completion)
   - 비용 (USD)
   - 모델명, 제공자

2. **Pipeline 단계 메트릭**
   - 단계별 Latency
   - 산출물 URI
   - 상태 (성공/실패)

3. **SUMO 실행 메트릭**
   - 시뮬레이션 시간
   - 차량 수, 완료 비율
   - 리소스 사용

4. **에러 로그**
   - 예외 타입, 메시지
   - 스택 트레이스
   - 컨텍스트 정보

---

## 구성 요소

### 1. ObservabilityContext

request_id, experiment_id, run_id 추적.

```python
from libs.common.observability import with_context, get_context

# 컨텍스트 설정
with with_context(experiment_id="exp_001", step_name="orchestrator"):
    # 모든 로그/메트릭에 자동 포함
    logger.info("Processing experiment")

# 컨텍스트 조회
context = get_context()
print(context.experiment_id)  # exp_001
```

**필드**:
- `request_id`: HTTP 요청 ID (자동 생성)
- `experiment_id`: 실험 ID
- `run_id`: 실행 ID (동일 실험의 여러 실행 구분)
- `user_id`: 사용자 ID
- `step_name`: 파이프라인 단계명
- `variant_id`: 시나리오 변형 ID

### 2. Structured Logger

JSON 포맷 로그 + 컨텍스트 자동 포함.

```python
from libs.common.observability import get_logger, configure_logging

# 로깅 설정 (앱 시작 시)
configure_logging(level="INFO", format_type="json")

# 로거 생성
logger = get_logger(__name__)

# 로그 출력
logger.info("Processing request", extra_fields={"status": "started"})
logger.error("Failed to connect", extra_fields={"host": "localhost", "port": 5432})
```

**출력 예시**:
```json
{
  "timestamp": "2026-05-07T10:00:00.123Z",
  "level": "INFO",
  "logger": "apps.orchestrator.main",
  "message": "Processing request",
  "module": "main",
  "function": "process",
  "line": 42,
  "context": {
    "request_id": "req_a1b2c3d4",
    "experiment_id": "exp_001",
    "step_name": "orchestrator"
  },
  "extra": {
    "status": "started"
  }
}
```

### 3. Metrics Collector

Prometheus 형식 메트릭 (향후 exporter 추가).

```python
from libs.common.observability import get_metrics_collector, Timer

metrics = get_metrics_collector()

# Counter
metrics.record_counter("requests_total", value=1.0, labels={"status": "success"})

# Gauge
metrics.record_gauge("active_connections", value=42.0)

# Histogram (latency)
metrics.record_histogram("request_duration_seconds", value=0.123)

# Timer (context manager)
with Timer("processing_time"):
    process_data()
```

### 4. LLM Metrics Logger

LLM 호출 메트릭 자동 수집.

```python
from libs.common.observability import LLMMetricsLogger

logger = LLMMetricsLogger()

with logger.track_call(model="claude-3-sonnet", provider="bedrock"):
    response = llm_client.generate(prompt)
    
    # 토큰 사용량 기록
    logger.record_tokens(
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens
    )
    
    # 비용 기록
    cost = calculate_bedrock_cost(...)
    logger.record_cost(cost)
```

**수집 데이터**:
- Latency (ms)
- Token 사용량 (prompt, completion, total)
- 비용 (USD)
- 모델명, 제공자
- 에러 (발생 시)

### 5. Pipeline Metrics Logger

Pipeline 단계별 메트릭 수집.

```python
from libs.common.observability import PipelineMetricsLogger

logger = PipelineMetricsLogger(experiment_id="exp_001")

# 단계 추적
with logger.track_step("orchestrator") as step:
    spec = orchestrator.parse(request)
    step.set_artifact("s3://bucket/spec.json")

with logger.track_step("scenario_builder") as step:
    plan = scenario_builder.build(spec)
    step.set_artifact("s3://bucket/plan.json")

# 완료
logger.finalize(status="completed", report_uri="s3://bucket/report.md")
```

**수집 데이터**:
- 단계별 Latency
- 산출물 URI
- 상태 (성공/실패)
- 에러 메시지

---

## 사용 가이드

### 1. 서비스 초기화 시 설정

```python
from fastapi import FastAPI
from libs.common.observability import configure_logging, with_context

app = FastAPI()

@app.on_event("startup")
def startup():
    # 로깅 설정
    configure_logging(level="INFO", format_type="json")
    print("✓ Logging configured")

@app.post("/process")
async def process_request(request: Request):
    # 컨텍스트 설정
    with with_context(request_id=request.headers.get("X-Request-ID")):
        # 처리
        result = await process(request)
        return result
```

### 2. LLM 호출 추적

```python
from libs.common.observability import LLMMetricsLogger, get_logger

logger = get_logger(__name__)
llm_logger = LLMMetricsLogger()

async def call_llm(prompt: str):
    with llm_logger.track_call(model="claude-3-sonnet", provider="bedrock"):
        try:
            response = await bedrock_client.generate(prompt)
            
            # 토큰 기록
            llm_logger.record_tokens(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
            
            # 비용 계산 및 기록
            cost = calculate_bedrock_cost(...)
            llm_logger.record_cost(cost)
            
            return response.text
            
        except Exception as e:
            llm_logger.record_error(e)
            raise
```

### 3. Pipeline 실행 추적

```python
from libs.common.observability import PipelineMetricsLogger, with_context

async def run_pipeline(request: PipelineExecutionRequest):
    # 컨텍스트 설정
    with with_context(experiment_id=request.experiment_id):
        logger = PipelineMetricsLogger(
            experiment_id=request.experiment_id,
            pipeline_type="e2e"
        )
        
        try:
            # 단계 1: Orchestrator
            with logger.track_step("orchestrator") as step:
                spec = await orchestrator.parse(request.user_request)
                step.set_artifact(spec_uri)
            
            # 단계 2: Scenario Builder
            with logger.track_step("scenario_builder") as step:
                plan = await scenario_builder.build(spec)
                step.set_artifact(plan_uri)
            
            # ... 다른 단계
            
            # 완료
            logger.finalize(status="completed", report_uri=report_uri)
            
        except Exception as e:
            logger.finalize(status="failed", error=str(e))
            raise
```

### 4. 에러 로깅

```python
from libs.common.observability import get_logger

logger = get_logger(__name__)

try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra_fields={
            "operation": "risky_operation",
            "error_type": type(e).__name__,
            "error_message": str(e),
        },
        exc_info=True  # 스택 트레이스 포함
    )
    raise
```

---

## CloudWatch Logs 분석

### Log Insights 쿼리 예시

**LLM 호출 Latency 분석**:
```
fields @timestamp, context.experiment_id, extra.llm_metrics.latency_ms
| filter message = "LLM call completed"
| stats avg(extra.llm_metrics.latency_ms) as avg_latency by extra.llm_metrics.model
```

**Pipeline 단계별 Latency**:
```
fields @timestamp, context.experiment_id, extra.step_name, extra.duration_ms
| filter message = "Pipeline step completed"
| stats avg(extra.duration_ms) as avg_duration by extra.step_name
```

**에러 분석**:
```
fields @timestamp, level, message, exception.type, exception.message
| filter level = "ERROR"
| stats count() by exception.type
```

**토큰 사용량 집계**:
```
fields @timestamp, context.experiment_id, extra.llm_metrics.total_tokens
| filter message = "LLM call completed"
| stats sum(extra.llm_metrics.total_tokens) as total_tokens by context.experiment_id
```

---

## 메트릭 목록

### System Metrics (Prometheus)

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `http_requests_total` | Counter | HTTP 요청 수 |
| `http_request_duration_seconds` | Histogram | HTTP 요청 Latency |
| `pipeline_executions_total` | Counter | Pipeline 실행 수 |
| `pipeline_execution_duration_seconds` | Histogram | Pipeline 전체 Latency |
| `pipeline_step_duration_seconds` | Histogram | Pipeline 단계별 Latency |
| `llm_call_latency_seconds` | Histogram | LLM 호출 Latency |
| `llm_tokens_total` | Counter | LLM 토큰 사용량 |
| `llm_cost_usd` | Counter | LLM 비용 |
| `llm_errors_total` | Counter | LLM 에러 수 |
| `sumo_execution_duration_seconds` | Histogram | SUMO 실행 시간 |
| `job_executions_total` | Counter | Kubernetes Job 실행 수 |

### Labels

모든 메트릭에 공통 레이블:
- `experiment_id`: 실험 ID
- `request_id`: 요청 ID
- `step`: 파이프라인 단계
- `status`: 성공/실패 상태

---

## Grafana 대시보드

### 1. Agent-T Overview

**패널**:
- Pipeline 실행 횟수 (시간별)
- 성공/실패율
- 평균 실행 시간
- 활성 실험 수

### 2. LLM Metrics

**패널**:
- LLM 호출 Latency (P50, P95, P99)
- 토큰 사용량 (시간별)
- 비용 (시간별, 누적)
- 모델별 비교

### 3. Pipeline Performance

**패널**:
- 단계별 Latency (히트맵)
- 병목 단계 식별
- 단계별 성공률

### 4. SUMO Execution

**패널**:
- SUMO Job 실행 시간
- Job 성공/실패율
- 리소스 사용 (CPU/메모리)

**대시보드 JSON**: `docs/grafana-dashboards/`

---

## AI 품질 평가 (향후 확장)

### Evaluation Pipeline

구조화된 로그를 기반으로 AI 품질 평가:

1. **LLM 응답 품질**
   - 프롬프트 효과성
   - 응답 일관성
   - Hallucination 탐지

2. **실험 재현성**
   - 동일 입력에 대한 결과 비교
   - 버전별 성능 변화

3. **비용 최적화**
   - 모델별 비용/성능 트레이드오프
   - 토큰 사용 최적화 기회

### 분석 도구

- OpenSearch Dashboard (로그 탐색)
- Jupyter Notebook (데이터 분석)
- Custom Evaluation Script

---

## 보안 고려사항

### 민감 정보 마스킹

로그에서 민감 정보 제거:
- 사용자 개인정보
- API 키, 토큰
- 내부 IP 주소

### 로그 보존 정책

- CloudWatch Logs: 30일
- S3 Archive: 1년
- OpenSearch: 90일

### 접근 제어

- Grafana: RBAC 기반 접근 제어
- CloudWatch Logs: IAM 정책
- OpenSearch: Fine-grained access control

---

## 다음 단계

### Phase 1 (현재)
- [x] 구조화된 로깅 구현
- [x] 컨텍스트 추적 (request_id, experiment_id)
- [x] LLM/Pipeline 메트릭 수집
- [x] Prometheus/Grafana placeholder

### Phase 2
- [ ] Prometheus exporter 구현 (`/metrics` 엔드포인트)
- [ ] Grafana 대시보드 생성
- [ ] CloudWatch Logs 통합
- [ ] AlertManager 알림 설정

### Phase 3
- [ ] OpenSearch 인덱싱
- [ ] AI 품질 평가 파이프라인
- [ ] 비용 최적화 분석
- [ ] Distributed Tracing (Jaeger/Zipkin)

---

## 참고

- [OpenTelemetry](https://opentelemetry.io/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [Grafana Documentation](https://grafana.com/docs/)
