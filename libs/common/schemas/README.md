# Common Schemas

**모듈 간 입출력 스키마** - 서비스 간 계약(contract) 정의

---

## 📋 개요

AI Agent T 플랫폼의 모든 서비스 간 데이터 교환 스키마를 정의합니다.

**설계 원칙**:
- **단일 진실 공급원**: 스키마는 한 곳에서만 정의
- **타입 안전성**: Pydantic v2 기반 런타임 검증
- **명확한 계약**: 생산자와 소비자 간 명확한 인터페이스
- **버전 관리**: 스키마 변경 시 호환성 유지

---

## 📁 스키마 목록

| 파일 | 스키마 | 생산자 | 소비자 |
|------|--------|--------|--------|
| `user_request.py` | `UserRequest` | API Service | Orchestrator |
| `experiment.py` | `ExperimentSpec` | Scenario Builder | Network/Demand Builder, Runner |
| `network.py` | `NetworkArtifact` | Network Builder | Demand Builder, Runner |
| `demand.py` | `DemandArtifact` | Demand Builder | Runner |
| `simulation.py` | `SimulationResult` | Simulator Runner | Analyzer |
| `analysis.py` | `KPIDataset` | Analyzer | Reporter |
| `report.py` | `ReportArtifact` | Reporter | API Service |
| `pipeline.py` | `PipelineRequest` | API Service | Pipeline Service |
| `logging.py` | `LogEntry` | 모든 서비스 | Observability |
| `versioning.py` | `ModelVersion`, `PromptVersion` | Agent Service | DB |

**총 라인 수**: 2,057 줄

---

## 🔑 주요 스키마 상세

### 1. UserRequest (user_request.py)

사용자의 자연어 요청을 표현합니다.

```python
from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    """사용자 자연어 요청"""
    user_request: str = Field(..., description="사용자 요구사항 (자연어)")
    experiment_id: Optional[str] = Field(None, description="실험 ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
```

**사용 예시**:
```python
from common.schemas import UserRequest

request = UserRequest(
    user_request="강남역 일대 교통량 20% 증가 시뮬레이션",
    experiment_id="exp_001"
)
```

---

### 2. ExperimentSpec (experiment.py)

Scenario Builder가 생성하는 실험 명세입니다.

```python
class ExperimentSpec(BaseModel):
    """실험 명세 - Scenario Builder 출력"""
    experiment_id: str
    scenario_type: str  # "demand_change", "network_change", "signal_optimization"
    location: LocationSpec
    baseline: BaselineConfig
    variants: List[VariantSpec]
    simulation_config: SimulationConfig
```

**사용 예시**:
```python
from common.schemas import ExperimentSpec

spec = ExperimentSpec(
    experiment_id="exp_001",
    scenario_type="demand_change",
    location=LocationSpec(
        area_name="강남역",
        bbox=[127.025, 37.495, 127.035, 37.505]
    ),
    variants=[
        VariantSpec(
            variant_id="baseline",
            demand_multiplier=1.0
        ),
        VariantSpec(
            variant_id="increased",
            demand_multiplier=1.2
        )
    ]
)
```

---

### 3. NetworkArtifact (network.py)

Network Builder가 생성하는 SUMO 도로망 산출물입니다.

```python
class NetworkArtifact(BaseModel):
    """SUMO 도로망 산출물"""
    network_file_uri: str  # s3://bucket/networks/exp_001.net.xml
    osm_source_uri: Optional[str]  # s3://bucket/osm/gangnam.osm
    edge_count: int
    junction_count: int
    metadata: NetworkMetadata
```

---

### 4. SimulationResult (simulation.py)

Simulator Runner가 생성하는 시뮬레이션 결과입니다.

```python
class SimulationResult(BaseModel):
    """SUMO 시뮬레이션 결과"""
    simulation_id: str
    variant_id: str
    status: str  # "completed", "failed"
    output_files: SimulationOutputFiles
    summary_statistics: SummaryStatistics
    execution_time_seconds: float
```

**포함 파일**:
- `tripinfo.xml`: 개별 차량 통행 정보
- `summary.xml`: 시뮬레이션 요약 통계
- `edgeData.xml`: 엣지별 교통량
- `laneData.xml`: 차선별 교통량

---

### 5. KPIDataset (analysis.py)

Analyzer가 생성하는 KPI 분석 결과입니다.

```python
class KPIDataset(BaseModel):
    """KPI 분석 결과"""
    experiment_id: str
    kpis: Dict[str, KPIMetric]
    comparison: Optional[VariantComparison]
    charts: List[ChartSpec]
```

**주요 KPI**:
- `avg_travel_time`: 평균 통행 시간 (초)
- `avg_waiting_time`: 평균 대기 시간 (초)
- `total_distance`: 총 주행 거리 (km)
- `throughput`: 처리량 (차량/시간)
- `congestion_index`: 혼잡도 지수

---

### 6. ReportArtifact (report.py)

Reporter가 생성하는 정책 리포트입니다.

```python
class ReportArtifact(BaseModel):
    """정책 리포트"""
    report_id: str
    experiment_id: str
    report_type: str  # "markdown", "pdf", "html"
    file_uri: str  # s3://bucket/reports/exp_001.md
    sections: List[ReportSection]
    recommendations: List[PolicyRecommendation]
```

---

## 📊 데이터 플로우

```
UserRequest (user_request.py)
    │
    ▼
Orchestrator
    │
    ▼
ExperimentSpec (experiment.py)
    │
    ├──▶ Network Builder ──▶ NetworkArtifact (network.py)
    │                              │
    └──▶ Demand Builder ◀──────────┘
                │
                ▼
         DemandArtifact (demand.py)
                │
                ▼
         Simulator Runner
                │
                ▼
        SimulationResult (simulation.py)
                │
                ▼
            Analyzer
                │
                ▼
         KPIDataset (analysis.py)
                │
                ▼
            Reporter
                │
                ▼
       ReportArtifact (report.py)
```

---

## 🔧 사용 가이드

### Import 방법

```python
# 방법 1: 개별 import (권장)
from common.schemas import UserRequest, ExperimentSpec

# 방법 2: 모듈 전체 import
from common.schemas.experiment import ExperimentSpec, VariantSpec

# 방법 3: 그룹 import
from common.schemas import (
    UserRequest,
    ExperimentSpec,
    NetworkArtifact,
    SimulationResult,
    KPIDataset,
    ReportArtifact
)
```

### 검증

Pydantic이 자동으로 타입 검증을 수행합니다.

```python
from common.schemas import ExperimentSpec
from pydantic import ValidationError

try:
    spec = ExperimentSpec(
        experiment_id="exp_001",
        scenario_type="invalid_type",  # ❌ 허용되지 않는 값
        # ... 필수 필드 누락
    )
except ValidationError as e:
    print(e.json())
```

### JSON 직렬화/역직렬화

```python
from common.schemas import ExperimentSpec

# 직렬화
spec = ExperimentSpec(...)
json_str = spec.model_dump_json()  # Pydantic v2

# 역직렬화
spec = ExperimentSpec.model_validate_json(json_str)  # Pydantic v2
```

### FastAPI 통합

```python
from fastapi import FastAPI
from common.schemas import UserRequest, ExperimentSpec

app = FastAPI()

@app.post("/orchestrator/parse", response_model=ExperimentSpec)
async def parse_request(request: UserRequest) -> ExperimentSpec:
    # 자동 검증 및 직렬화
    spec = orchestrator.parse(request.user_request)
    return spec
```

---

## 🔄 버전 관리

### Breaking Changes

스키마 변경 시 호환성을 유지합니다.

**Breaking Change 예시**:
- 필수 필드 추가
- 필드 타입 변경
- 필드 삭제

**대응 방법**:
1. 새 버전 스키마 생성 (예: `ExperimentSpecV2`)
2. 구 버전 지원 기간 설정
3. 마이그레이션 가이드 제공

### Non-Breaking Changes

**허용되는 변경**:
- 선택 필드 추가 (`Optional[...]`)
- Enum 값 추가
- 기본값 추가
- 주석/문서 수정

---

## 📚 스키마 파일 상세

### experiment.py (278줄)

**주요 클래스**:
- `ExperimentSpec`: 실험 명세 전체
- `LocationSpec`: 지리적 영역
- `VariantSpec`: 시나리오 변형
- `SimulationConfig`: 시뮬레이션 설정
- `BaselineConfig`: 기준선 설정

### network.py (183줄)

**주요 클래스**:
- `NetworkArtifact`: 도로망 산출물
- `OSMConfig`: OpenStreetMap 설정
- `NetworkMetadata`: 도로망 메타데이터
- `EdgeInfo`: 엣지 정보
- `JunctionInfo`: 교차로 정보

### demand.py (181줄)

**주요 클래스**:
- `DemandArtifact`: 교통 수요 산출물
- `ODMatrix`: Origin-Destination 행렬
- `TimeProfile`: 시간대별 수요 패턴
- `VehicleType`: 차량 타입
- `RouteDistribution`: 경로 분포

### simulation.py (198줄)

**주요 클래스**:
- `SimulationResult`: 시뮬레이션 결과
- `SimulationOutputFiles`: 출력 파일 URI
- `SummaryStatistics`: 요약 통계
- `VehicleMetrics`: 차량별 메트릭
- `EdgeMetrics`: 엣지별 메트릭

### analysis.py (245줄)

**주요 클래스**:
- `KPIDataset`: KPI 데이터셋
- `KPIMetric`: 개별 KPI
- `VariantComparison`: 변형 간 비교
- `StatisticalTest`: 통계적 검정 결과
- `ChartSpec`: 차트 명세

### report.py (224줄)

**주요 클래스**:
- `ReportArtifact`: 리포트 산출물
- `ReportSection`: 리포트 섹션
- `PolicyRecommendation`: 정책 권고
- `ConfidenceLevel`: 신뢰 수준
- `ImpactAssessment`: 영향 평가

### pipeline.py (114줄)

**주요 클래스**:
- `PipelineRequest`: E2E 파이프라인 요청
- `PipelineResponse`: 파이프라인 응답
- `PipelineStatus`: 파이프라인 상태
- `StepResult`: 단계별 결과

### logging.py (155줄)

**주요 클래스**:
- `LogEntry`: 구조화된 로그 항목
- `LogLevel`: 로그 레벨
- `LogContext`: 로그 컨텍스트
- `ExceptionInfo`: 예외 정보

### versioning.py (256줄)

**주요 클래스**:
- `ModelVersion`: LLM 모델 버전
- `PromptVersion`: 프롬프트 버전
- `SchemaVersion`: 스키마 버전
- `VersionMetadata`: 버전 메타데이터

---

## 🧪 테스트

```bash
# 스키마 테스트
pytest libs/common/schemas/tests/ -v

# 특정 스키마 테스트
pytest libs/common/schemas/tests/test_experiment.py -v

# 커버리지
pytest libs/common/schemas/tests/ --cov=libs.common.schemas --cov-report=html
```

---

## 📖 참고 문서

- [docs/schemas-reference.md](../../../docs/schemas-reference.md) - 전체 스키마 레퍼런스
- [Pydantic Documentation](https://docs.pydantic.dev/latest/) - Pydantic v2 공식 문서
- [CLAUDE.md](../../../CLAUDE.md) - 프로젝트 컨텍스트

---

## ⚠️ 주의사항

### 스키마 변경 시

1. **하위 호환성 유지**: 기존 서비스가 영향받지 않도록
2. **테스트 작성**: 새 스키마에 대한 테스트 추가
3. **문서 업데이트**: `docs/schemas-reference.md` 갱신
4. **마이그레이션 가이드**: Breaking change 시 제공

### import 규칙

- ✅ `from common.schemas import ExperimentSpec`
- ✅ `from common.schemas.experiment import ExperimentSpec`
- ❌ `from packages.common_schema import ExperimentSpec` (deprecated)

---

**Last Updated**: 2026-05-07
