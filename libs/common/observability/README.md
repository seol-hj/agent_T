# Observability Library

구조화된 로깅, 메트릭 수집, 컨텍스트 추적.

---

## 개요

AI Agent T 플랫폼의 관측성 라이브러리.

**주요 기능**:
- 구조화된 JSON 로그
- request_id, experiment_id, run_id 추적
- LLM 호출 메트릭 (latency, token, cost)
- Pipeline 단계별 메트릭
- SUMO 실행 메트릭
- Prometheus 형식 메트릭 (향후 exporter)

---

## 설치

```bash
# 이미 common library에 포함되어 있음
pip install -r libs/common/requirements.txt
```

---

## 빠른 시작

### 1. 로깅 설정

```python
from libs.common.observability import configure_logging

# 앱 시작 시 한 번만 호출
configure_logging(level="INFO", format_type="json")
```

### 2. 로거 사용

```python
from libs.common.observability import get_logger

logger = get_logger(__name__)

logger.info("Processing request")
logger.error("Failed to connect", extra_fields={"host": "localhost"})
```

### 3. 컨텍스트 추적

```python
from libs.common.observability import with_context

with with_context(experiment_id="exp_001", step_name="orchestrator"):
    # 모든 로그에 자동 포함
    logger.info("Processing experiment")
```

### 4. LLM 메트릭

```python
from libs.common.observability import LLMMetricsLogger

llm_logger = LLMMetricsLogger()

with llm_logger.track_call(model="claude-3-sonnet", provider="bedrock"):
    response = llm_client.generate(prompt)
    llm_logger.record_tokens(prompt_tokens=1000, completion_tokens=500)
    llm_logger.record_cost(0.0045)
```

### 5. Pipeline 메트릭

```python
from libs.common.observability import PipelineMetricsLogger

logger = PipelineMetricsLogger(experiment_id="exp_001")

with logger.track_step("orchestrator") as step:
    spec = orchestrator.parse(request)
    step.set_artifact("s3://bucket/spec.json")

logger.finalize(status="completed", report_uri="s3://bucket/report.md")
```

---

## 구성 요소

### 1. ObservabilityContext

request_id, experiment_id, run_id 추적.

```python
from libs.common.observability import create_context, set_context, get_context

# 컨텍스트 생성
context = create_context(experiment_id="exp_001", step_name="orchestrator")
set_context(context)

# 컨텍스트 조회
current = get_context()
print(current.experiment_id)  # exp_001
```

### 2. Structured Logger

JSON 포맷 로그 + 컨텍스트 자동 포함.

```python
from libs.common.observability import get_logger

logger = get_logger(__name__)
logger.info("Message", extra_fields={"key": "value"})
```

**출력**:
```json
{
  "timestamp": "2026-05-07T10:00:00.123Z",
  "level": "INFO",
  "logger": "my.module",
  "message": "Message",
  "context": {
    "request_id": "req_a1b2c3d4",
    "experiment_id": "exp_001"
  },
  "extra": {
    "key": "value"
  }
}
```

### 3. Metrics Collector

Prometheus 형식 메트릭 (향후 exporter).

```python
from libs.common.observability import get_metrics_collector, Timer

metrics = get_metrics_collector()

metrics.record_counter("requests_total", value=1.0)
metrics.record_gauge("active_connections", value=42.0)
metrics.record_histogram("request_duration_seconds", value=0.123)

with Timer("processing_time"):
    process_data()
```

### 4. LLM Metrics Logger

LLM 호출 메트릭 자동 수집.

```python
from libs.common.observability import LLMMetricsLogger

llm_logger = LLMMetricsLogger()

with llm_logger.track_call(model="claude-3-sonnet", provider="bedrock"):
    response = llm_client.generate(prompt)
    llm_logger.record_tokens(prompt_tokens=1000, completion_tokens=500)
    llm_logger.record_cost(0.0045)
```

### 5. Pipeline Metrics Logger

Pipeline 단계별 메트릭 수집.

```python
from libs.common.observability import PipelineMetricsLogger

logger = PipelineMetricsLogger(experiment_id="exp_001")

with logger.track_step("orchestrator") as step:
    spec = orchestrator.parse(request)
    step.set_artifact("s3://bucket/spec.json")

logger.finalize(status="completed", report_uri="s3://bucket/report.md")
```

---

## FastAPI 통합

```python
from fastapi import FastAPI, Request
from libs.common.observability import configure_logging, with_context, get_logger

app = FastAPI()
logger = get_logger(__name__)

@app.on_event("startup")
def startup():
    configure_logging(level="INFO", format_type="json")

@app.middleware("http")
async def add_context(request: Request, call_next):
    # 요청마다 컨텍스트 생성
    request_id = request.headers.get("X-Request-ID", generate_request_id())
    
    with with_context(request_id=request_id):
        response = await call_next(request)
        return response

@app.post("/process")
async def process(request: ProcessRequest):
    with with_context(experiment_id=request.experiment_id):
        logger.info("Processing request")
        result = await process_data(request)
        return result
```

---

## 테스트

```bash
# 단위 테스트
pytest libs/common/observability/tests/test_context.py -v

# 예제 실행
python libs/common/observability/examples/usage_example.py
```

---

## 로그 구조

### 기본 필드

```json
{
  "timestamp": "2026-05-07T10:00:00.123Z",
  "level": "INFO",
  "logger": "module.name",
  "message": "Log message",
  "module": "module",
  "function": "function_name",
  "line": 42
}
```

### 컨텍스트 필드

```json
{
  "context": {
    "request_id": "req_a1b2c3d4",
    "experiment_id": "exp_001",
    "run_id": "run_001",
    "user_id": "user_123",
    "step_name": "orchestrator",
    "variant_id": "baseline",
    "created_at": "2026-05-07T10:00:00.000Z",
    "metadata": {}
  }
}
```

### 예외 필드

```json
{
  "exception": {
    "type": "ValueError",
    "message": "Invalid input",
    "traceback": "..."
  }
}
```

### 추가 필드 (extra_fields)

```json
{
  "extra": {
    "custom_field": "value",
    "status": "processing"
  }
}
```

---

## 메트릭

### Counter

```python
metrics.record_counter("requests_total", value=1.0, labels={"status": "success"})
```

### Gauge

```python
metrics.record_gauge("active_connections", value=42.0)
```

### Histogram (Latency)

```python
metrics.record_histogram("request_duration_seconds", value=0.123)
```

### Timer

```python
with Timer("processing_time", labels={"operation": "transform"}):
    process_data()
```

---

## CloudWatch Logs 분석

### Log Insights 쿼리

**실험별 LLM 비용**:
```
fields @timestamp, context.experiment_id, extra.llm_metrics.estimated_cost
| filter message = "LLM call completed"
| stats sum(extra.llm_metrics.estimated_cost) as total_cost by context.experiment_id
```

**단계별 Latency**:
```
fields @timestamp, extra.step_name, extra.duration_ms
| filter message = "Pipeline step completed"
| stats avg(extra.duration_ms) as avg_latency by extra.step_name
```

**에러 분석**:
```
fields @timestamp, level, message, exception.type
| filter level = "ERROR"
| stats count() by exception.type
```

---

## 디렉토리 구조

```
libs/common/observability/
├── __init__.py
├── context.py              # ObservabilityContext
├── logger.py               # Structured Logger
├── metrics.py              # Metrics Collector
├── llm_metrics.py          # LLM Metrics Logger
├── pipeline_metrics.py     # Pipeline Metrics Logger
├── tests/
│   └── test_context.py
├── examples/
│   └── usage_example.py
└── README.md
```

---

## 다음 단계

### Phase 2
- [ ] Prometheus exporter (`/metrics` 엔드포인트)
- [ ] Grafana 대시보드 생성
- [ ] CloudWatch Logs 통합

### Phase 3
- [ ] Distributed Tracing (OpenTelemetry)
- [ ] AI 품질 평가 파이프라인
- [ ] 비용 최적화 분석

---

## 참고

- [docs/observability.md](../../../docs/observability.md) - 전체 관측성 아키텍처
- [k8s/monitoring/INSTALL.md](../../../k8s/monitoring/INSTALL.md) - Prometheus/Grafana 설치
