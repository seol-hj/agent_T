# Pipeline Service

E2E 교통 시뮬레이션 파이프라인 실행 서비스.

사용자의 자연어 요청부터 최종 정책 리포트까지 전체 흐름을 오케스트레이션합니다.

---

## 아키텍처

Pipeline Service는 7개 모듈을 순차적으로 호출하여 E2E 파이프라인을 실행합니다:

```
User Request
     ↓
1. Orchestrator → ExperimentSpec
     ↓
2. Scenario Builder → ScenarioPlan + NetworkBuildRequests + DemandBuildRequests
     ↓
3. Network Builder (Baseline + Alternatives) → NetworkArtifacts
     ↓
4. Demand Builder (Baseline + Alternatives) → DemandArtifacts
     ↓
5. Simulator Runner (Baseline + Alternatives) → SimulationRunArtifacts
     ↓
6. Analyzer → AnalysisResult (KPI 비교)
     ↓
7. Reporter → ReportArtifact (정책 리포트)
     ↓
Report URI
```

---

## 주요 기능

### 1. **전체 파이프라인 실행**

단일 API 호출로 전체 7단계를 자동 실행.

```bash
POST /pipeline/run
```

**Request**:
```json
{
  "user_request": "강남역 일대 교통량 20% 증가 시뮬레이션",
  "experiment_id": "exp_001",
  "dry_run": false,
  "skip_steps": []
}
```

**Response**:
```json
{
  "version": "1.0.0",
  "execution_id": "exec_001",
  "experiment_id": "exp_001",
  "status": "completed",
  "steps": [
    {
      "step_name": "orchestrator",
      "status": "completed",
      "started_at": "2026-05-07T10:00:00",
      "completed_at": "2026-05-07T10:00:05",
      "duration_ms": 5000,
      "artifact_uri": null,
      "error_message": null
    },
    ...
  ],
  "report_uri": "s3://reports/report_001.md",
  "total_duration_ms": 45000,
  "error_message": null,
  "created_at": "2026-05-07T10:00:00"
}
```

### 2. **Dry Run 모드**

SUMO 시뮬레이터를 실행하지 않고 더미 데이터로 전체 흐름을 테스트.

```json
{
  "user_request": "테스트",
  "experiment_id": "exp_dry",
  "dry_run": true,
  "skip_steps": []
}
```

- SUMO 설치 없이도 전체 파이프라인 테스트 가능
- 빠른 E2E 검증

### 3. **Skip Steps**

특정 단계를 건너뛰고 파이프라인 실행 (디버깅/테스트용).

```json
{
  "user_request": "테스트",
  "experiment_id": "exp_skip",
  "dry_run": false,
  "skip_steps": ["simulator_runner", "analyzer"]
}
```

- 각 단계는 독립적으로 스킵 가능
- 스킵된 단계는 `status: "skipped"`로 표시

### 4. **단계별 상태 추적**

각 단계의 실행 상태를 실시간으로 추적:

- `pending`: 대기 중
- `running`: 실행 중
- `completed`: 완료
- `failed`: 실패
- `skipped`: 스킵됨

### 5. **에러 처리**

중간 단계 실패 시:
- 해당 단계에 `error_message` 기록
- 이후 단계는 `pending` 상태로 유지
- 전체 파이프라인 `status: "failed"` 반환

---

## API 엔드포인트

### `GET /health`

헬스 체크.

```bash
curl http://localhost:8000/health
```

### `GET /ready`

준비 상태 체크 (서비스 초기화 완료 여부).

```bash
curl http://localhost:8000/ready
```

### `POST /pipeline/run`

E2E 파이프라인 실행.

**Parameters**:
- `user_request` (string, required): 자연어 요청
- `experiment_id` (string, optional): 실험 ID (미제공 시 자동 생성)
- `dry_run` (boolean, optional): Dry Run 모드 (기본: false)
- `skip_steps` (array, optional): 스킵할 단계 목록 (기본: [])

**Example**:
```bash
curl -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "강남역 일대 교통량 20% 증가 시뮬레이션",
    "experiment_id": "exp_001",
    "dry_run": false,
    "skip_steps": []
  }'
```

### `GET /`

서비스 정보 및 파이프라인 단계 목록.

```bash
curl http://localhost:8000/
```

---

## 환경 변수

서비스 URL은 환경 변수로 설정:

```bash
ORCHESTRATOR_URL=http://orchestrator:8001
SCENARIO_BUILDER_URL=http://scenario-builder:8002
NETWORK_BUILDER_URL=http://network-builder:8003
DEMAND_BUILDER_URL=http://demand-builder:8004
SIMULATOR_RUNNER_URL=http://simulator-runner:8005
ANALYZER_URL=http://analyzer:8006
REPORTER_URL=http://reporter:8007
PORT=8000
```

---

## 로컬 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 서비스 시작

```bash
python -m uvicorn apps.pipeline.main:app --host 0.0.0.0 --port 8000
```

### 3. 테스트

```bash
pytest apps/pipeline/tests/ -v
```

---

## Docker 실행

### 1. 빌드

```bash
docker build -f apps/pipeline/Dockerfile -t pipeline-service:latest .
```

### 2. 실행

```bash
docker run -p 8000:8000 \
  -e ORCHESTRATOR_URL=http://orchestrator:8001 \
  -e SCENARIO_BUILDER_URL=http://scenario-builder:8002 \
  -e NETWORK_BUILDER_URL=http://network-builder:8003 \
  -e DEMAND_BUILDER_URL=http://demand-builder:8004 \
  -e SIMULATOR_RUNNER_URL=http://simulator-runner:8005 \
  -e ANALYZER_URL=http://analyzer:8006 \
  -e REPORTER_URL=http://reporter:8007 \
  pipeline-service:latest
```

---

## 테스트

### 단위 테스트

```bash
pytest apps/pipeline/tests/test_pipeline_service.py -v
```

### E2E 테스트

```bash
pytest apps/pipeline/tests/test_e2e.py -v
```

### 전체 테스트

```bash
pytest apps/pipeline/tests/ -v
```

---

## 디렉토리 구조

```
apps/pipeline/
├── main.py                      # FastAPI 애플리케이션
├── services/
│   ├── __init__.py
│   └── pipeline_service.py      # 파이프라인 오케스트레이션 로직
├── tests/
│   ├── __init__.py
│   ├── test_pipeline_service.py # 단위 테스트
│   └── test_e2e.py              # E2E 통합 테스트
├── requirements.txt             # Python 의존성
├── Dockerfile                   # Docker 이미지 정의
└── README.md                    # 문서 (현재 파일)
```

---

## 사용 예시

### 1. 기본 파이프라인 실행

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/pipeline/run",
        json={
            "user_request": "강남역 일대 차선 1개 증설 효과 분석",
            "experiment_id": "exp_lane_increase"
        }
    )
    result = response.json()
    print(f"Report URI: {result['report_uri']}")
```

### 2. Dry Run 모드로 빠른 테스트

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/pipeline/run",
        json={
            "user_request": "테스트",
            "experiment_id": "exp_test",
            "dry_run": True
        }
    )
    result = response.json()
    print(f"Status: {result['status']}")
```

### 3. 특정 단계만 실행 (디버깅)

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/pipeline/run",
        json={
            "user_request": "테스트",
            "experiment_id": "exp_debug",
            "skip_steps": ["simulator_runner", "analyzer", "reporter"]
        }
    )
    result = response.json()
    # Orchestrator, Scenario Builder, Network Builder, Demand Builder만 실행
```

---

## 에러 처리

### Orchestrator 실패

```json
{
  "status": "failed",
  "error_message": "Failed at orchestrator: LLM Gateway error",
  "steps": [
    {
      "step_name": "orchestrator",
      "status": "failed",
      "error_message": "LLM Gateway error"
    },
    ...
  ]
}
```

### Network Builder 실패

```json
{
  "status": "failed",
  "error_message": "Failed at network_builder: Network generation failed",
  "steps": [
    {
      "step_name": "orchestrator",
      "status": "completed"
    },
    {
      "step_name": "scenario_builder",
      "status": "completed"
    },
    {
      "step_name": "network_builder",
      "status": "failed",
      "error_message": "Network generation failed"
    },
    ...
  ]
}
```

---

## 다음 단계

- [ ] Kubernetes manifest 작성 (`k8s/apps/pipeline.yaml`)
- [ ] Terraform으로 EKS에 배포
- [ ] Argo CD로 GitOps 파이프라인 구성
- [ ] 실시간 진행 상태 스트리밍 (WebSocket)
- [ ] 파이프라인 실행 이력 조회 API
- [ ] 중간 재시작 기능 (특정 단계부터 재개)

---

## 참고

- [Orchestrator README](../orchestrator/README.md)
- [Scenario Builder README](../scenario-builder/README.md)
- [Network Builder README](../network-builder/README.md)
- [Demand Builder README](../demand-builder/README.md)
- [Simulator Runner README](../simulator-runner/README.md)
- [Analyzer README](../analyzer/README.md)
- [Reporter README](../reporter/README.md)
