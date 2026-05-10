# 스키마 참조 문서

AI Agent T 플랫폼의 공통 Pydantic Schema 참조 문서.

## 개요

모든 서비스 간 데이터 교환에 사용되는 공통 스키마를 Pydantic으로 정의했습니다.  
각 스키마는 `schema_version` 필드를 포함하며, 산출물(Artifact)은 `uri`와 `created_at` 필드를 갖습니다.

**위치**: `libs/common/schemas/`

## 스키마 목록

### 1. 사용자 요구사항

#### `UserRequest`
사용자가 자연어로 입력한 교통 시뮬레이션 요구사항.

**파일**: `user_request.py`

**주요 필드**:
- `request_id`: 요청 고유 ID
- `user_id`: 사용자 ID
- `raw_input`: 원본 자연어 텍스트
- `language`: 입력 언어 (기본값: "ko")
- `tags`: 사용자 정의 태그
- `context`: 추가 컨텍스트 정보

**예시**:
```python
UserRequest(
    request_id="req-20260507-123456",
    user_id="user-001",
    raw_input="서울 강남구 출퇴근 시간대 교통량을 분석하고 신호등 최적화 효과를 비교하고 싶습니다",
    language="ko"
)
```

---

### 2. 실험 명세

#### `ExperimentSpec`
자연어 입력에서 추출된 구조화된 실험 명세.

**파일**: `experiment.py`

**주요 필드**:
- `experiment_id`: 실험 고유 ID
- `request_id`: 원본 요청 ID
- `title`: 실험 제목
- `description`: 실험 설명
- `location`: 시뮬레이션 위치 (bbox, osm_query 등)
- `time_settings`: 시간 설정 (시작/종료 시간, 시간대)
- `traffic_settings`: 교통 설정 (차량 수, 차종 분포)
- `objectives`: 실험 목표 리스트
- `constraints`: 제약 조건 리스트
- `generated_by`: LLM 메타데이터 (모델 ID, 프롬프트 버전)

**예시**:
```python
ExperimentSpec(
    experiment_id="exp-20260507-001",
    request_id="req-20260507-123456",
    title="강남구 출퇴근 시간대 신호등 최적화 효과 분석",
    location={
        "region": "서울특별시 강남구",
        "bbox": [127.0276, 37.4959, 127.0948, 37.5219]
    },
    time_settings={"start_time": "07:00", "end_time": "09:00"},
    traffic_settings={"vehicle_count": 5000},
    objectives=["통행 시간 단축", "배출량 감소"]
)
```

---

#### `ScenarioPlan`
Base 시나리오와 Alternative 시나리오(들)을 포함하는 계획.

**파일**: `experiment.py`

**주요 필드**:
- `plan_id`: 계획 ID
- `experiment_id`: 실험 ID
- `baseline`: Baseline 시나리오 (ScenarioVariant, variant_type="baseline")
- `alternatives`: Alternative 시나리오 리스트 (최소 1개, variant_type="alternative")
- `comparison_objectives`: 비교 목표

**예시**:
```python
ScenarioPlan(
    plan_id="plan-20260507-001",
    experiment_id="exp-20260507-001",
    baseline=ScenarioVariant(
        variant_id="base-001",
        variant_type="baseline",
        name="현재 신호 체계",
        parameters={"signal_cycle": 120}
    ),
    alternatives=[
        ScenarioVariant(
            variant_id="alt-signal-001",
            variant_type="alternative",
            name="최적화된 신호 체계",
            parameters={"signal_cycle": 90}
        )
    ],
    comparison_objectives=["평균 통행 시간 단축", "배출량 감소"]
)
```

---

#### `ScenarioVariant`
개별 시나리오 변형 (Baseline 또는 Alternative).

**파일**: `experiment.py`

**주요 필드**:
- `variant_id`: 변형 ID
- `variant_type`: ScenarioType.BASELINE | ScenarioType.ALTERNATIVE
- `name`: 변형 이름
- `description`: 변형 설명
- `parameters`: 시나리오 파라미터 (dict)

---

### 3. 도로망 (Network)

#### `NetworkBuildRequest`
OSM 데이터로부터 SUMO 도로망 생성 요청.

**파일**: `network.py`

**주요 필드**:
- `request_id`: 요청 ID
- `experiment_id`: 실험 ID
- `variant_id`: 시나리오 변형 ID
- `osm_source`: OSM 데이터 소스 (type, bbox, query)
- `network_options`: 도로망 생성 옵션
- `modifications`: 도로망 수정 사항 (Alternative용)

**예시**:
```python
NetworkBuildRequest(
    request_id="netreq-20260507-001",
    experiment_id="exp-20260507-001",
    variant_id="base-001",
    osm_source={
        "type": "bbox",
        "bbox": [127.0276, 37.4959, 127.0948, 37.5219]
    }
)
```

---

#### `NetworkArtifact`
생성된 SUMO 도로망 파일.

**파일**: `network.py`

**주요 필드**:
- `artifact_id`: 산출물 ID
- `uri`: 도로망 파일 URI (s3:// 또는 file://)
- `file_format`: "net.xml"
- `file_size_bytes`: 파일 크기
- `statistics`: 도로망 통계 (nodes, edges, junctions, traffic_lights)
- `created_at`: 생성 시각
- `generated_by`: 생성 도구 (예: "netconvert-1.18.0")

**예시**:
```python
NetworkArtifact(
    artifact_id="net-20260507-001",
    uri="s3://agent-t-networks/exp-20260507-001/base-001/network.net.xml",
    file_format="net.xml",
    file_size_bytes=1024576,
    statistics={"nodes": 1234, "edges": 2345, "junctions": 456}
)
```

---

### 4. 수요 (Demand)

#### `DemandBuildRequest`
교통 수요 생성 요청 (통행 패턴 및 차량 경로).

**파일**: `demand.py`

**주요 필드**:
- `request_id`: 요청 ID
- `experiment_id`: 실험 ID
- `variant_id`: 시나리오 변형 ID
- `network_artifact_id`: 도로망 산출물 ID
- `demand_settings`: 수요 생성 설정 (vehicle_count, vehicle_types, trip_distribution)

**예시**:
```python
DemandBuildRequest(
    request_id="demreq-20260507-001",
    experiment_id="exp-20260507-001",
    variant_id="base-001",
    network_artifact_id="net-20260507-001",
    demand_settings={
        "vehicle_count": 5000,
        "vehicle_types": {"passenger": 0.8, "bus": 0.1, "truck": 0.1}
    }
)
```

---

#### `DemandArtifact`
생성된 차량 경로 파일.

**파일**: `demand.py`

**주요 필드**:
- `artifact_id`: 산출물 ID
- `uri`: 경로 파일 URI
- `file_format`: "rou.xml"
- `file_size_bytes`: 파일 크기
- `statistics`: 수요 통계 (total_vehicles, vehicles_by_type, total_trips)
- `created_at`: 생성 시각
- `generated_by`: 생성 도구 (예: "duarouter-1.18.0")

**예시**:
```python
DemandArtifact(
    artifact_id="dem-20260507-001",
    uri="s3://agent-t-demand/exp-20260507-001/base-001/routes.rou.xml",
    file_format="rou.xml",
    file_size_bytes=2048000,
    statistics={"total_vehicles": 5000, "avg_trip_length_km": 8.5}
)
```

---

### 5. 시뮬레이션 (Simulation)

#### `SimulationRunRequest`
SUMO 시뮬레이션 실행 요청.

**파일**: `simulation.py`

**주요 필드**:
- `request_id`: 요청 ID
- `experiment_id`: 실험 ID
- `variant_id`: 시나리오 변형 ID
- `network_artifact_id`: 도로망 산출물 ID
- `demand_artifact_id`: 수요 산출물 ID
- `simulation_settings`: 시뮬레이션 설정 (step_length, begin, end, output_types)

**예시**:
```python
SimulationRunRequest(
    request_id="simreq-20260507-001",
    experiment_id="exp-20260507-001",
    variant_id="base-001",
    network_artifact_id="net-20260507-001",
    demand_artifact_id="dem-20260507-001",
    simulation_settings={
        "step_length": 1.0,
        "begin": 0,
        "end": 7200,
        "output_types": ["tripinfo", "summary", "emissions"]
    }
)
```

---

#### `SimulationRunArtifact`
SUMO 실행 후 생성된 결과 파일들.

**파일**: `simulation.py`

**주요 필드**:
- `artifact_id`: 산출물 ID
- `uri`: 시뮬레이션 결과 디렉토리 URI
- `output_files`: 출력 파일 목록 (dict: tripinfo, summary, emissions 등)
- `status`: "completed" | "failed" | "timeout"
- `statistics`: 시뮬레이션 통계 (total_vehicles, completed_trips, teleports, runtime_seconds)
- `created_at`: 생성 시각
- `generated_by`: 생성 도구 (예: "sumo-1.18.0")
- `error_message`: 오류 메시지 (실패 시)

**예시**:
```python
SimulationRunArtifact(
    artifact_id="sim-20260507-001",
    uri="s3://agent-t-simulations/exp-20260507-001/base-001/",
    output_files={
        "tripinfo": "s3://.../tripinfo.xml",
        "summary": "s3://.../summary.xml"
    },
    status="completed",
    statistics={"total_vehicles": 5000, "completed_trips": 4987}
)
```

---

### 6. 분석 (Analysis)

#### `AnalysisResult`
시뮬레이션 산출물 분석 결과 및 KPI 비교.

**파일**: `analysis.py`

**주요 필드**:
- `analysis_id`: 분석 ID
- `experiment_id`: 실험 ID
- `simulation_artifact_ids`: 분석 대상 시뮬레이션 산출물 ID 리스트
- `kpi_comparison`: KPI 비교 결과 (KPIComparison)
- `detailed_metrics`: 상세 지표
- `created_at`: 생성 시각
- `generated_by`: 생성 정보

**예시**:
```python
AnalysisResult(
    analysis_id="ana-20260507-001",
    experiment_id="exp-20260507-001",
    simulation_artifact_ids=["sim-20260507-001", "sim-20260507-002"],
    kpi_comparison=KPIComparison(...)
)
```

---

#### `KPIComparison`
Baseline과 Alternative 시나리오 간 성능 비교.

**파일**: `analysis.py`

**주요 필드**:
- `baseline`: BaselineKPI
- `alternatives`: list[AlternativeKPI] (최소 1개)
- `best_alternative_id`: 최적 Alternative 변형 ID
- `recommendation_summary`: 권장사항 요약

---

#### `BaselineKPI`
Baseline 시나리오의 성능 지표.

**파일**: `analysis.py`

**주요 필드**:
- `variant_id`: Baseline 변형 ID
- `avg_trip_duration_seconds`: 평균 통행 시간
- `avg_waiting_time_seconds`: 평균 대기 시간
- `total_co2_kg`: 총 CO2 배출량
- `avg_speed_kmh`: 평균 속도
- `completed_trips`: 완료된 통행 수
- `teleports`: 텔레포트 발생 횟수

**예시**:
```python
BaselineKPI(
    variant_id="base-001",
    avg_trip_duration_seconds=1245.6,
    avg_waiting_time_seconds=89.3,
    total_co2_kg=2456.8,
    avg_speed_kmh=28.5,
    completed_trips=4987,
    teleports=13
)
```

---

#### `AlternativeKPI`
Alternative 시나리오의 성능 지표 및 개선율.

**파일**: `analysis.py`

**주요 필드**:
- `variant_id`: Alternative 변형 ID
- `avg_trip_duration_seconds`: 평균 통행 시간
- `avg_waiting_time_seconds`: 평균 대기 시간
- `total_co2_kg`: 총 CO2 배출량
- `avg_speed_kmh`: 평균 속도
- `completed_trips`: 완료된 통행 수
- `teleports`: 텔레포트 발생 횟수
- **`improvements`**: Baseline 대비 개선율 (%) — dict 형식

**예시**:
```python
AlternativeKPI(
    variant_id="alt-signal-001",
    avg_trip_duration_seconds=1045.2,
    avg_waiting_time_seconds=62.7,
    total_co2_kg=2089.4,
    avg_speed_kmh=34.2,
    completed_trips=4995,
    teleports=5,
    improvements={
        "trip_duration": -16.1,   # 16.1% 단축
        "waiting_time": -29.8,    # 29.8% 단축
        "co2_emission": -15.0,    # 15.0% 감소
        "speed": 20.0             # 20.0% 증가
    }
)
```

---

### 7. 리포트 (Report)

#### `ReportArtifact`
정책 의사결정을 위한 최종 리포트.

**파일**: `report.py`

**주요 필드**:
- `artifact_id`: 산출물 ID
- `experiment_id`: 실험 ID
- `analysis_id`: 분석 ID
- `title`: 리포트 제목
- `uri`: 리포트 파일 URI
- `file_format`: "pdf" | "markdown" | "html"
- `sections`: 리포트 섹션 리스트 (ReportSection)
- `executive_summary`: 경영진 요약
- `recommendations`: 권장사항 리스트
- `created_at`: 생성 시각
- `generated_by`: 생성 정보 (LLM 메타데이터)

**예시**:
```python
ReportArtifact(
    artifact_id="rep-20260507-001",
    experiment_id="exp-20260507-001",
    analysis_id="ana-20260507-001",
    title="강남구 출퇴근 시간대 신호등 최적화 효과 분석 보고서",
    uri="s3://agent-t-reports/exp-20260507-001/report.pdf",
    file_format="pdf",
    sections=[...],
    executive_summary="신호 체계 최적화로 통행 시간 16.1% 단축 가능",
    recommendations=["신호 주기 단축", "녹색 시간 조정"]
)
```

---

#### `ReportSection`
리포트 내 개별 섹션.

**파일**: `report.py`

**주요 필드**:
- `section_id`: 섹션 ID
- `title`: 섹션 제목
- `content`: 섹션 내용 (마크다운 형식)
- `order`: 섹션 순서
- `visualizations`: 시각화 자료 목록 (Optional)

**예시**:
```python
ReportSection(
    section_id="executive-summary",
    title="경영진 요약",
    content="## 주요 발견사항\n\n- 통행 시간 16.1% 단축\n- 배출량 15.0% 감소",
    order=1
)
```

---

### 8. 로깅 (Logging)

#### `AgentLog`
Agent 실행 중 발생하는 이벤트 로그.

**파일**: `logging.py`

**주요 필드**:
- `log_id`: 로그 ID
- `timestamp`: 로그 발생 시각
- `level`: LogLevel (debug | info | warning | error | critical)
- `agent_name`: 에이전트 이름
- `experiment_id`: 실험 ID (Optional)
- `request_id`: 요청 ID (Optional)
- `message`: 로그 메시지
- `context`: 추가 컨텍스트 정보 (Optional)
- `error_details`: 오류 상세 정보 (Optional)
- `llm_metadata`: LLM 호출 메타데이터 (Optional)

**예시**:
```python
AgentLog(
    log_id="log-20260507-123456-001",
    level=LogLevel.INFO,
    agent_name="scenario-builder",
    experiment_id="exp-20260507-001",
    message="시나리오 생성 완료",
    context={"variant_count": 2, "duration_ms": 1250.5}
)
```

---

#### `LogLevel` (Enum)
로그 레벨.

**파일**: `logging.py`

**값**:
- `DEBUG = "debug"`
- `INFO = "info"`
- `WARNING = "warning"`
- `ERROR = "error"`
- `CRITICAL = "critical"`

---

### 9. 버전 관리 (Versioning)

#### `ModelVersion`
LLM 모델 버전 정보 및 메타데이터.

**파일**: `versioning.py`

**주요 필드**:
- `model_id`: 모델 ID
- `model_name`: 모델 이름
- `provider`: 모델 제공자 (bedrock, openai, local)
- `version`: 버전 번호
- `capabilities`: 모델 능력 리스트
- `context_window`: 컨텍스트 윈도우 (토큰 수)
- `max_output_tokens`: 최대 출력 토큰 수
- `supports_streaming`: 스트리밍 지원 여부
- `cost_per_1k_input_tokens`: 1K 입력 토큰당 비용 (USD)
- `cost_per_1k_output_tokens`: 1K 출력 토큰당 비용 (USD)
- `deprecated`: 폐기 여부
- `replacement_model_id`: 대체 모델 ID (Optional)
- `notes`: 비고

**예시**:
```python
ModelVersion(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    model_name="Claude 3 Sonnet",
    provider="bedrock",
    version="20240229-v1:0",
    capabilities=["text-generation", "structured-output"],
    context_window=200000,
    max_output_tokens=4096,
    supports_streaming=True
)
```

---

#### `PromptVersion`
LLM 프롬프트 템플릿 버전 관리.

**파일**: `versioning.py`

**주요 필드**:
- `prompt_id`: 프롬프트 ID
- `prompt_name`: 프롬프트 이름
- `version`: 버전 번호
- `agent_name`: 사용하는 에이전트 이름
- `template`: 프롬프트 템플릿 내용
- `template_variables`: 템플릿 변수 리스트
- `expected_output_format`: 기대 출력 형식 (json, yaml, markdown)
- `output_schema_ref`: 출력 스키마 참조 (Optional)
- `compatible_models`: 호환 가능한 모델 ID 리스트
- `active`: 활성화 여부
- `performance_metrics`: 성능 지표 (Optional)
- `changelog`: 변경 이력 (Optional)

**예시**:
```python
PromptVersion(
    prompt_id="scenario-gen-v2.0",
    prompt_name="시나리오 생성 프롬프트",
    version="v2.0",
    agent_name="scenario-builder",
    template="당신은 교통 시뮬레이션 시나리오를 생성하는 AI 전문가입니다...",
    template_variables=["user_input", "location"],
    expected_output_format="json",
    output_schema_ref="ExperimentSpec",
    compatible_models=["anthropic.claude-3-sonnet-20240229-v1:0"]
)
```

---

## 스키마 설계 원칙

### 1. **공통 필드**
모든 스키마는 `schema_version` 필드를 포함하여 향후 버전 관리를 지원합니다.

```python
schema_version: str = Field(default="1.0", description="스키마 버전")
```

### 2. **산출물 (Artifact) 구조**
모든 Artifact 스키마는 다음 필드를 포함합니다:
- `artifact_id`: 산출물 고유 ID
- `uri`: 파일 URI (s3://, file:// 등)
- `file_size_bytes` 또는 `file_format`: 파일 메타데이터
- `statistics`: 산출물 통계
- `created_at`: 생성 시각
- `generated_by`: 생성 도구/버전 (Optional)

### 3. **Baseline vs Alternative 분리**
실험 시나리오는 명확히 구분됩니다:
- **Baseline**: 현재 상태 (`ScenarioType.BASELINE`)
- **Alternative**: 비교 대상 (`ScenarioType.ALTERNATIVE`)

분석 결과도 동일하게 구분:
- `BaselineKPI`: Baseline 시나리오의 성능 지표
- `AlternativeKPI`: Alternative 시나리오의 성능 지표 + **개선율 (improvements)**

### 4. **ID 체계**
일관된 ID 명명 규칙:
- `req-YYYYMMDD-HHMMSS`: UserRequest
- `exp-YYYYMMDD-NNN`: ExperimentSpec
- `netreq-YYYYMMDD-NNN`: NetworkBuildRequest
- `net-YYYYMMDD-NNN`: NetworkArtifact
- `demreq-YYYYMMDD-NNN`: DemandBuildRequest
- `dem-YYYYMMDD-NNN`: DemandArtifact
- `simreq-YYYYMMDD-NNN`: SimulationRunRequest
- `sim-YYYYMMDD-NNN`: SimulationRunArtifact
- `ana-YYYYMMDD-NNN`: AnalysisResult
- `rep-YYYYMMDD-NNN`: ReportArtifact

### 5. **Pydantic Field 활용**
모든 필드는 `Field()`를 사용하여 메타데이터를 제공합니다:
```python
field_name: Type = Field(
    ...,  # required 또는 default 값
    description="필드 설명",
    examples=["예시값"]
)
```

### 6. **JSON 예시 제공**
각 스키마의 `Config.json_schema_extra`에 완전한 JSON 예시를 포함합니다.

### 7. **LLM 메타데이터 추적**
LLM으로 생성된 스키마는 `generated_by` 필드에 메타데이터를 기록:
```python
generated_by: Optional[dict] = Field(
    default=None,
    description="생성 정보 (LLM 메타데이터)",
    examples=[{
        "model_id": "anthropic.claude-3-sonnet",
        "provider": "bedrock",
        "prompt_version": "scenario-gen-v2.0",
        "latency_ms": 1250.5
    }]
)
```

---

## 사용 예시

### 전체 워크플로우 예시

```python
from common.schemas import (
    UserRequest,
    ExperimentSpec,
    ScenarioPlan,
    NetworkBuildRequest,
    NetworkArtifact,
    DemandBuildRequest,
    DemandArtifact,
    SimulationRunRequest,
    SimulationRunArtifact,
    AnalysisResult,
    KPIComparison,
    BaselineKPI,
    AlternativeKPI,
    ReportArtifact,
)

# 1. 사용자 요청
user_req = UserRequest(
    request_id="req-001",
    user_id="user-001",
    raw_input="강남구 출퇴근 시간대 신호등 최적화"
)

# 2. 실험 명세 생성 (LLM)
exp_spec = ExperimentSpec(
    experiment_id="exp-001",
    request_id=user_req.request_id,
    title="강남구 신호등 최적화",
    description="출퇴근 시간대 교통 혼잡 완화",
    location={"region": "강남구", "bbox": [...]},
    time_settings={...},
    traffic_settings={...},
    objectives=["통행 시간 단축"]
)

# 3. 시나리오 계획
scenario_plan = ScenarioPlan(
    plan_id="plan-001",
    experiment_id=exp_spec.experiment_id,
    baseline=ScenarioVariant(...),
    alternatives=[ScenarioVariant(...)]
)

# 4. 도로망 생성
net_req = NetworkBuildRequest(...)
net_artifact = NetworkArtifact(...)

# 5. 수요 생성
dem_req = DemandBuildRequest(...)
dem_artifact = DemandArtifact(...)

# 6. 시뮬레이션 실행
sim_req = SimulationRunRequest(...)
sim_artifact = SimulationRunArtifact(...)

# 7. 분석
analysis = AnalysisResult(
    analysis_id="ana-001",
    experiment_id=exp_spec.experiment_id,
    simulation_artifact_ids=["sim-001", "sim-002"],
    kpi_comparison=KPIComparison(
        baseline=BaselineKPI(...),
        alternatives=[AlternativeKPI(...)],
        best_alternative_id="alt-001",
        recommendation_summary="통행 시간 16.1% 단축"
    )
)

# 8. 리포트 생성
report = ReportArtifact(
    artifact_id="rep-001",
    experiment_id=exp_spec.experiment_id,
    analysis_id=analysis.analysis_id,
    title="교통 분석 보고서",
    ...
)
```

---

## 테스트

### 검증 테스트 실행

```bash
# pytest 사용 (pytest 설치 필요)
python3 -m pytest libs/common/tests/test_schemas.py -v

# 구조 확인 (의존성 없음)
bash scripts/check-schema-structure.sh
```

### 주요 테스트 케이스
- 필수 필드 검증
- Baseline/Alternative 분리 검증
- ID 연계 검증 (request_id, experiment_id 등)
- JSON 직렬화/역직렬화
- 워크플로우 통합 테스트

---

## 다음 단계

1. **실제 데이터 검증**: 각 서비스에서 실제 데이터로 스키마 검증
2. **스키마 마이그레이션**: 버전 변경 시 마이그레이션 스크립트 작성
3. **API 문서 자동 생성**: Pydantic 스키마에서 OpenAPI 스펙 자동 생성
4. **타입 체크**: mypy 등으로 타입 정확성 검증

---

**작성일**: 2026-05-07  
**버전**: 1.0  
**작성자**: AI Agent T Team
