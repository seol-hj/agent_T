# Analyzer

시뮬레이션 결과 분석 서비스. SUMO 출력 XML 파일에서 KPI를 추출하고 Baseline vs Alternative 시나리오를 비교한다.

## 개요

- **입력**: `AnalysisRequest` (JSON) + Baseline/Alternative 시뮬레이션 아티팩트
- **출력**: `AnalysisResult` (JSON) + KPI 비교 + 개선율
- **주요 기능**:
  - SUMO XML 파싱 (tripinfo, summary, queue, emission)
  - KPI 추출 (통행 시간, 대기 시간, 속도, 대기열, 배출량 등)
  - 시나리오 비교 및 개선율 계산
  - 종합 평가 점수 산출

## 디렉토리 구조

```
analyzer/
├── main.py                     # FastAPI 앱
├── parsers/                    # SUMO XML 파서
│   └── sumo_result_parser.py   # tripinfo/summary/queue/emission 파서
├── services/
│   ├── kpi_engine.py           # KPI 계산 엔진
│   ├── scenario_comparator.py  # 시나리오 비교기
│   └── analysis_service.py     # 메인 분석 서비스
├── tests/
│   ├── fixtures/               # 샘플 XML 데이터
│   │   ├── sample_tripinfo.xml
│   │   ├── sample_summary.xml
│   │   ├── sample_queue.xml
│   │   └── sample_emission.xml
│   ├── test_sumo_result_parser.py
│   ├── test_kpi_engine.py
│   ├── test_scenario_comparator.py
│   └── test_api.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## 주요 컴포넌트

### 1. SumoResultParser

SUMO 출력 XML 파일 파싱.

**지원 파일**:
- `tripinfo.xml`: 개별 차량 통행 정보
- `summary.xml`: 타임스텝별 요약 통계
- `queue.xml`: 엣지별 대기열 정보
- `emission.xml`: 차량별 배출량 정보

**파싱 결과**:
```python
@dataclass
class TripInfo:
    vehicle_id: str
    depart_time: float
    arrival_time: float
    duration: float
    route_length: float
    waiting_time: float
    waiting_count: int
    time_loss: float
    vehicle_type: str
    speed_factor: float
```

### 2. KPIEngine

파싱 결과로부터 KPI 계산.

**추출 KPI**:

| KPI | 단위 | 설명 |
|-----|------|------|
| `average_travel_time` | seconds | 평균 통행 시간 |
| `average_waiting_time` | seconds | 평균 대기 시간 |
| `average_speed` | m/s | 평균 속도 |
| `average_time_loss` | seconds | 평균 시간 손실 |
| `average_queue_length` | meters | 평균 대기열 길이 |
| `max_queue_length` | meters | 최대 대기열 길이 |
| `completed_vehicle_count` | count | 완료 차량 수 |
| `total_route_length` | meters | 총 주행 거리 |
| `total_co2` | mg | 총 CO2 배출량 |
| `total_co` | mg | 총 CO 배출량 |
| `total_nox` | mg | 총 NOx 배출량 |
| `total_pmx` | mg | 총 미세먼지 배출량 |
| `total_fuel` | ml | 총 연료 소비 |
| `simulation_duration` | seconds | 시뮬레이션 총 시간 |
| `total_vehicles_loaded` | count | 로드된 총 차량 수 |

### 3. ScenarioComparator

Baseline vs Alternative 비교 및 개선율 계산.

**개선율 계산 규칙**:
- **감소가 좋은 지표**: 통행 시간, 대기 시간, 대기열, 배출량 등
  - 감소하면 양수 개선율
- **증가가 좋은 지표**: 속도, 완료 차량 수 등
  - 증가하면 양수 개선율

**종합 점수 산출**:
주요 지표에 가중치를 부여하여 종합 개선 점수 계산:
- 평균 통행 시간: 25%
- 평균 대기 시간: 20%
- 평균 속도: 15%
- 평균 대기열 길이: 15%
- 총 CO2: 15%
- 완료 차량 수: 10%

**요약 생성**:
개선/악화된 주요 지표를 기반으로 자연어 요약 생성.

### 4. AnalysisService

전체 분석 흐름 관리:

1. `AnalysisRequest` 파싱
2. Baseline 시뮬레이션 결과 다운로드
3. Alternative 시뮬레이션 결과 다운로드
4. SUMO XML 파싱
5. KPI 추출 (Baseline, Alternative)
6. 시나리오 비교
7. 개선율 계산
8. 종합 점수 및 요약 생성
9. `AnalysisResult` 반환

## API 엔드포인트

### POST /analysis/run

시뮬레이션 결과 분석.

**요청**:
```json
{
  "analysis_request": {
    "schema_version": "1.0",
    "request_id": "req-ana-001",
    "experiment_id": "exp-001",
    "baseline_simulation": {
      "schema_version": "1.0",
      "artifact_id": "sim-001-baseline",
      "variant_id": "baseline",
      "outputs": {
        "tripinfo": "s3://bucket/exp-001/baseline/tripinfo.xml",
        "summary": "s3://bucket/exp-001/baseline/summary.xml",
        "queue": "s3://bucket/exp-001/baseline/queue.xml",
        "emission": "s3://bucket/exp-001/baseline/emission.xml"
      }
    },
    "alternative_simulations": [
      {
        "schema_version": "1.0",
        "artifact_id": "sim-001-alternative",
        "variant_id": "alternative",
        "outputs": {
          "tripinfo": "s3://bucket/exp-001/alternative/tripinfo.xml",
          "summary": "s3://bucket/exp-001/alternative/summary.xml",
          "queue": "s3://bucket/exp-001/alternative/queue.xml",
          "emission": "s3://bucket/exp-001/alternative/emission.xml"
        }
      }
    ]
  }
}
```

**응답** (`AnalysisResult`):
```json
{
  "schema_version": "1.0",
  "analysis_id": "ana-001",
  "request_id": "req-ana-001",
  "experiment_id": "exp-001",
  "kpi_comparison": {
    "baseline_kpis": {
      "average_travel_time": 125.0,
      "average_waiting_time": 12.0,
      "average_speed": 4.16,
      "average_queue_length": 12.83,
      "completed_vehicle_count": 100,
      "total_co2": 16590.0
    },
    "alternative_kpis": {
      "average_travel_time": 110.0,
      "average_waiting_time": 9.6,
      "average_speed": 4.58,
      "average_queue_length": 10.26,
      "completed_vehicle_count": 100,
      "total_co2": 14931.0
    },
    "improvements": {
      "average_travel_time": 12.0,
      "average_waiting_time": 20.0,
      "average_speed": 10.1,
      "average_queue_length": 20.0,
      "total_co2": 10.0
    }
  },
  "overall_score": 14.5,
  "summary": "Alternative 시나리오가 전반적으로 우수합니다. 평균 통행 시간 12.0% 개선, 평균 대기 시간 20.0% 개선, 평균 속도 10.1% 개선, CO2 배출량 10.0% 개선.",
  "created_at": "2026-05-07T12:00:00",
  "processing_time_ms": 250.5,
  "analyzed_by": "analyzer-v0.1.0"
}
```

### GET /health

헬스 체크.

### GET /ready

준비 상태 체크.

### GET /

서비스 정보 및 지원 KPI 목록.

## 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export STORAGE_PROVIDER=local
export STORAGE_BASE_PATH=/tmp/analysis
export PORT=8005

# 서비스 시작
python -m uvicorn analyzer.main:app --host 0.0.0.0 --port 8005 --reload
```

## Docker 실행

```bash
# 이미지 빌드
docker build -t analyzer:latest -f apps/analyzer/Dockerfile .

# 컨테이너 실행
docker run -d \
  --name analyzer \
  -p 8005:8005 \
  -e STORAGE_PROVIDER=local \
  -e STORAGE_BASE_PATH=/app/data/analysis \
  analyzer:latest
```

## 테스트

```bash
# 모든 테스트 실행
pytest apps/analyzer/tests/ -v

# 특정 테스트 실행
pytest apps/analyzer/tests/test_sumo_result_parser.py -v
pytest apps/analyzer/tests/test_kpi_engine.py -v
pytest apps/analyzer/tests/test_scenario_comparator.py -v
pytest apps/analyzer/tests/test_api.py -v

# 커버리지
pytest apps/analyzer/tests/ --cov=apps.analyzer --cov-report=html
```

## 설정

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `STORAGE_PROVIDER` | `local` | 스토리지 제공자 (`local` / `s3`) |
| `STORAGE_BASE_PATH` | `/app/data/analysis` | 로컬 저장 경로 |
| `PORT` | `8005` | 서비스 포트 |

## KPI 상세

### Trip 기반 KPI

**tripinfo.xml**에서 추출:

- **average_travel_time**: 출발부터 도착까지의 평균 시간
- **average_waiting_time**: 정지 상태로 대기한 평균 시간
- **average_speed**: 평균 주행 속도 (거리 / 시간)
- **average_time_loss**: 최적 속도 대비 손실 시간
- **completed_vehicle_count**: 목적지에 도착한 차량 수

### Queue 기반 KPI

**queue.xml**에서 추출:

- **average_queue_length**: 모든 엣지의 평균 대기열 길이
- **max_queue_length**: 최대 대기열 길이 (혼잡도 지표)

### Emission 기반 KPI

**emission.xml**에서 추출:

- **total_co2**: 총 이산화탄소 배출량 (환경 영향)
- **total_co**: 총 일산화탄소 배출량
- **total_nox**: 총 질소산화물 배출량
- **total_pmx**: 총 미세먼지 배출량
- **total_fuel**: 총 연료 소비량

### Summary 기반 KPI

**summary.xml**에서 추출:

- **simulation_duration**: 시뮬레이션 총 실행 시간
- **total_vehicles_loaded**: 로드된 총 차량 수

## 개선율 해석

**양수 (+)**: Alternative가 Baseline보다 좋음 (개선)
**음수 (-)**: Alternative가 Baseline보다 나쁨 (악화)
**0**: 변화 없음

**예시**:
- `average_travel_time: 12.0` → 통행 시간 12% 감소 (개선)
- `average_speed: -5.0` → 속도 5% 감소 (악화)
- `total_co2: 10.0` → CO2 10% 감소 (개선)

## 종합 점수

**0 이상**: 전반적으로 개선
**0 이하**: 전반적으로 악화

점수가 높을수록 Alternative 시나리오가 우수함.

## 확장 가능성

### 새 KPI 추가

1. `KPIEngine`에 계산 메서드 추가
2. `calculate_kpis()`에 KPI 추가
3. `ScenarioComparator._calculate_improvements()`에 비교 규칙 추가
4. 테스트 작성

**예시**:
```python
def _calculate_average_fuel_efficiency(self, trips: list[TripInfo], emissions: list[EmissionData]) -> float:
    """평균 연료 효율 (km/L)"""
    if not trips or not emissions:
        return 0.0
    total_distance_km = sum(t.route_length for t in trips) / 1000
    total_fuel_l = sum(e.fuel for e in emissions) / 1000
    return total_distance_km / total_fuel_l if total_fuel_l > 0 else 0.0
```

### 가중치 커스터마이징

`ScenarioComparator.calculate_overall_score()`의 `weights` dict 수정.

### 다중 Alternative 비교

현재는 첫 번째 Alternative만 비교. `AnalysisService.analyze()`를 수정하여 여러 Alternative 동시 비교 가능.

## 제약 사항

- **초기 구현**: 첫 번째 Alternative만 비교
- **파싱 에러**: 개별 항목 파싱 실패 시 건너뜀 (로그 없음)
- **정규화**: KPI 값의 스케일 차이 고려 안 함 (향후 정규화 필요)

## 다음 단계

1. **다중 Alternative 비교**: 여러 Alternative를 동시에 비교하고 순위 매기기
2. **시계열 분석**: 타임스텝별 KPI 추이 분석
3. **공간 분석**: 엣지/교차로별 KPI 분석
4. **통계적 유의성 검증**: 개선율의 통계적 유의성 판단
5. **시각화**: KPI 차트, 히트맵 생성
6. **LLM 통합**: 자연어 분석 리포트 생성

## 참고

- [SUMO Tripinfo Output](https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html)
- [SUMO Summary Output](https://sumo.dlr.de/docs/Simulation/Output/Summary.html)
- [SUMO Queue Output](https://sumo.dlr.de/docs/Simulation/Output/QueueOutput.html)
- [SUMO Emission Output](https://sumo.dlr.de/docs/Models/Emissions.html)
