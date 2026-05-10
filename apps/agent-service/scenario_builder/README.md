# Scenario Builder Service

ExperimentSpec으로부터 시나리오 계획 및 빌드 요청을 생성하는 서비스.

## 역할

- ExperimentSpec 입력 → ScenarioPlan + 빌드 요청 출력
- Baseline 시나리오 생성 (현재 상태)
- Alternative 시나리오 생성 (비교 대상)
- 시나리오별 도로망 변경 사항 정의
- 시나리오별 교통 수요 변경 사항 정의
- NetworkBuildRequest 및 DemandBuildRequest 생성

## 핵심 기능

### 1. 시나리오 생성

**입력**: ExperimentSpec (실험 명세)  
**출력**: ScenarioPlan + NetworkBuildRequest 목록 + DemandBuildRequest 목록

**지원 요청 타입**:
- `demand_increase`: 교통량 증가 시나리오 (기본 20% 증가)
- `lane_change`: 차로 변경 시나리오 (주요 도로 +1 차로)
- `signal_timing_change`: 신호 타이밍 변경 시나리오 (최적화된 신호 주기)

### 2. Baseline 시나리오

현재 상태를 나타내는 Base 시나리오:
- 도로망 변경 없음
- 교통량 변경 없음 (demand_multiplier = 1.0)
- modifications = []

### 3. Alternative 시나리오

비교 대상이 되는 시나리오:
- **demand_increase**: vehicle_count * 1.2 (20% 증가)
- **lane_change**: 주요 도로의 차로 수 +1
- **signal_timing_change**: 신호 주기 90초, 녹색 시간 55%

### 4. 빌드 요청 생성

각 변형(Baseline + Alternatives)마다:
- **NetworkBuildRequest 1개**: OSM → SUMO 도로망 생성
- **DemandBuildRequest 1개**: 교통 수요 및 차량 경로 생성

## 아키텍처

```
┌─────────────────────────────┐
│   FastAPI Main              │
│   (main.py)                 │
└──────────┬──────────────────┘
           │
           ├─► ScenarioGenerator (services/scenario_generator.py)
           │   ├─► _create_baseline_variant()
           │   ├─► _create_alternative_variants()
           │   │   ├─► _create_demand_increase_variant()
           │   │   ├─► _create_lane_change_variant()
           │   │   └─► _create_signal_timing_variant()
           │   ├─► _create_scenario_plan()
           │   ├─► _create_network_requests()
           │   └─► _create_demand_requests()
           │
           └─► Pydantic Schemas (libs/common/schemas/)
               ├─► ExperimentSpec
               ├─► ScenarioPlan
               ├─► NetworkBuildRequest
               └─► DemandBuildRequest
```

## 설치 및 실행

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 시작
python -m uvicorn apps.scenario-builder.main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t scenario-builder:latest -f apps/scenario-builder/Dockerfile .

# 컨테이너 실행
docker run -d -p 8001:8001 scenario-builder:latest
```

## API 엔드포인트

### 1. `/scenario-builder/build` (POST)

ExperimentSpec으로부터 시나리오를 생성합니다.

**요청**:
```json
{
  "experiment_spec": {
    "experiment_id": "exp-20260507-001",
    "request_id": "req-20260507-123456",
    "title": "강남구 신호등 최적화",
    "description": "출퇴근 시간대 교통 혼잡 완화",
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
    "objectives": ["통행 시간 단축", "배출량 감소"],
    "constraints": []
  },
  "request_type": "signal_timing_change"
}
```

**응답**:
```json
{
  "scenario_plan": {
    "schema_version": "1.0",
    "plan_id": "plan-001",
    "experiment_id": "exp-20260507-001",
    "baseline": {
      "variant_id": "base-001",
      "variant_type": "baseline",
      "name": "현재 상태 (Baseline)",
      "description": "변경 사항 없이 현재 도로망 및 교통 수요 상태",
      "parameters": {
        "modifications": [],
        "demand_multiplier": 1.0,
        "network_changes": null
      }
    },
    "alternatives": [
      {
        "variant_id": "alt-signal-001",
        "variant_type": "alternative",
        "name": "신호 체계 최적화",
        "description": "AI 기반으로 최적화된 신호등 타이밍",
        "parameters": {
          "modifications": [
            {
              "type": "traffic_light",
              "target": "all_junctions",
              "cycle": 90,
              "green_split": 0.55,
              "description": "신호 주기 90초, 녹색 시간 55%"
            }
          ],
          "demand_multiplier": 1.0,
          "network_changes": {
            "signal_timing": {
              "strategy": "optimize_cycle",
              "cycle_seconds": 90,
              "green_time_ratio": 0.55
            }
          }
        }
      }
    ],
    "comparison_objectives": ["통행 시간 단축", "배출량 감소"],
    "created_at": "2026-05-07T12:00:00Z"
  },
  "network_requests": [
    {
      "schema_version": "1.0",
      "request_id": "netreq-001-base-001",
      "experiment_id": "exp-20260507-001",
      "variant_id": "base-001",
      "osm_source": {
        "type": "bbox",
        "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
        "query": "Gangnam-gu, Seoul, South Korea"
      },
      "network_options": {
        "vehicle_types": ["passenger", "bus", "truck"],
        "tls_guess": true,
        "speed_limits": true,
        "geometry_remove": true
      },
      "modifications": null,
      "created_at": "2026-05-07T12:00:00Z"
    },
    {
      "schema_version": "1.0",
      "request_id": "netreq-001-alt-signal-001",
      "experiment_id": "exp-20260507-001",
      "variant_id": "alt-signal-001",
      "osm_source": {...},
      "network_options": {...},
      "modifications": [
        {
          "type": "traffic_light",
          "strategy": "optimize_cycle",
          "cycle_seconds": 90,
          "green_time_ratio": 0.55,
          "target_junctions": "all"
        }
      ],
      "created_at": "2026-05-07T12:00:00Z"
    }
  ],
  "demand_requests": [
    {
      "schema_version": "1.0",
      "request_id": "demreq-001-base-001",
      "experiment_id": "exp-20260507-001",
      "variant_id": "base-001",
      "network_artifact_id": "net-001-base-001",
      "demand_settings": {
        "vehicle_count": 5000,
        "start_time": 25200,
        "end_time": 32400,
        "vehicle_types": {"passenger": 0.8, "bus": 0.1, "truck": 0.1},
        "trip_distribution": "random",
        "departure_distribution": "uniform"
      },
      "created_at": "2026-05-07T12:00:00Z"
    },
    {
      "schema_version": "1.0",
      "request_id": "demreq-001-alt-signal-001",
      "experiment_id": "exp-20260507-001",
      "variant_id": "alt-signal-001",
      "network_artifact_id": "net-001-alt-signal-001",
      "demand_settings": {
        "vehicle_count": 5000,
        "start_time": 25200,
        "end_time": 32400,
        "vehicle_types": {"passenger": 0.8, "bus": 0.1, "truck": 0.1},
        "trip_distribution": "random",
        "departure_distribution": "uniform"
      },
      "created_at": "2026-05-07T12:00:00Z"
    }
  ],
  "experiment_id": "exp-20260507-001",
  "baseline_variant_id": "base-001",
  "alternative_variant_ids": ["alt-signal-001"],
  "processing_time_ms": 5.2,
  "created_at": "2026-05-07T12:00:00.123Z"
}
```

### 2. `/health` (GET)

헬스 체크.

### 3. `/ready` (GET)

준비 상태 체크.

### 4. `/` (GET)

서비스 정보 및 지원 요청 타입.

## 시나리오 변형 생성 로직

### demand_increase (교통량 증가)

```python
{
  "variant_id": "alt-demand-001",
  "variant_type": "alternative",
  "name": "교통량 20% 증가",
  "description": "차량 수가 20% 증가했을 때의 교통 상황",
  "parameters": {
    "modifications": [],
    "demand_multiplier": 1.2,  # 20% 증가
    "network_changes": null
  }
}
```

**DemandBuildRequest**:
- `vehicle_count`: 5000 → 6000 (20% 증가)
- `network_artifact_id`: Baseline과 동일 (도로망 변경 없음)

### lane_change (차로 변경)

```python
{
  "variant_id": "alt-lane-001",
  "variant_type": "alternative",
  "name": "주요 도로 차로 추가 (+1)",
  "description": "주요 병목 구간의 차로를 1개 추가",
  "parameters": {
    "modifications": [
      {
        "type": "lane_change",
        "target": "major_edges",
        "lane_delta": 1
      }
    ],
    "demand_multiplier": 1.0,
    "network_changes": {
      "lane_modifications": {
        "strategy": "increase_major_roads",
        "lane_delta": 1
      }
    }
  }
}
```

**NetworkBuildRequest**:
- `modifications`: lane_change 포함
- Network Builder가 실제 적용할 edge 선택

### signal_timing_change (신호 타이밍 변경)

```python
{
  "variant_id": "alt-signal-001",
  "variant_type": "alternative",
  "name": "신호 체계 최적화",
  "description": "AI 기반으로 최적화된 신호등 타이밍",
  "parameters": {
    "modifications": [
      {
        "type": "traffic_light",
        "target": "all_junctions",
        "cycle": 90,
        "green_split": 0.55
      }
    ],
    "demand_multiplier": 1.0,
    "network_changes": {
      "signal_timing": {
        "strategy": "optimize_cycle",
        "cycle_seconds": 90,
        "green_time_ratio": 0.55
      }
    }
  }
}
```

**NetworkBuildRequest**:
- `modifications`: traffic_light 포함
- Network Builder가 모든 junction에 적용

## 테스트

```bash
# 단위 테스트
pytest apps/scenario-builder/tests/test_scenario_generator.py -v

# API 테스트
pytest apps/scenario-builder/tests/test_api.py -v

# 전체 테스트
pytest apps/scenario-builder/tests/ -v
```

### 주요 테스트 케이스

**ScenarioGenerator 테스트** (16개):
- ✅ demand_increase 시나리오 생성
- ✅ lane_change 시나리오 생성
- ✅ signal_timing_change 시나리오 생성
- ✅ Baseline 변형 생성
- ✅ Alternative 변형 생성 (각 타입별)
- ✅ NetworkBuildRequest 생성
- ✅ DemandBuildRequest 생성
- ✅ 시간 변환 (HH:MM → 초)
- ✅ 네트워크 수정사항 변환
- ✅ 고유 ID 검증
- ✅ 변형-요청 일치 검증

**API 테스트** (14개):
- ✅ 헬스 체크
- ✅ 준비 상태 체크
- ✅ 루트 엔드포인트
- ✅ demand_increase 빌드
- ✅ lane_change 빌드
- ✅ signal_timing_change 빌드
- ✅ 잘못된 요청 타입
- ✅ 잘못된 ExperimentSpec
- ✅ 필수 필드 누락
- ✅ demand_multiplier 적용 검증
- ✅ 네트워크 수정사항 검증
- ✅ 변형-요청 ID 일치 검증

## 설계 결정 사항

### 1. 결정론적 시나리오 생성

LLM을 사용하지 않고 규칙 기반으로 시나리오를 생성합니다.

**이유**:
- 예측 가능한 결과
- 빠른 실행 속도
- 테스트 용이성
- 비용 절감

**향후 개선**:
- LLM을 활용한 더 다양한 Alternative 생성
- 사용자 의도를 더 잘 반영하는 변형 생성

### 2. 각 변형당 별도 빌드 요청

Baseline과 각 Alternative마다 독립적인 NetworkBuildRequest와 DemandBuildRequest를 생성합니다.

**이유**:
- Network Builder와 Demand Builder가 병렬 실행 가능
- 변형별로 독립적인 산출물 관리
- 실패 시 다른 변형에 영향 없음

**트레이드오프**:
- Baseline 도로망을 재사용할 수 있는 경우에도 별도 요청 생성
- 향후 최적화: Baseline 도로망 재사용 로직 추가

### 3. 기본 증가율 및 변경사항

각 요청 타입별 기본값을 하드코딩했습니다.

**현재 기본값**:
- demand_increase: 20% 증가
- lane_change: +1 차로
- signal_timing_change: 90초 주기, 55% 녹색

**향후 개선**:
- ExperimentSpec의 objectives에서 증가율 추출
- 사용자가 명시한 값 우선 사용
- LLM으로 적절한 변경 폭 제안

### 4. modifications 형식

네트워크 수정사항을 추상적인 형태로 전달하고, 실제 적용은 Network Builder가 결정합니다.

**예시**:
```json
{
  "type": "lane_change",
  "strategy": "increase_major_roads",
  "lane_delta": 1,
  "target_edges": "major"
}
```

**이유**:
- Scenario Builder는 의도만 전달
- Network Builder가 실제 도로망을 분석하여 적용
- 유연한 구현 변경 가능

## 다음 단계

1. **Network Builder 구현**: NetworkBuildRequest → NetworkArtifact
2. **Demand Builder 구현**: DemandBuildRequest → DemandArtifact
3. **LLM 기반 Alternative 생성**: 더 다양하고 창의적인 시나리오
4. **사용자 정의 변경 폭**: objectives에서 증가율/변경량 추출
5. **다중 Alternative**: 하나의 요청 타입에 여러 변형 생성
6. **Baseline 도로망 재사용**: demand_increase 시 네트워크 재생성 불필요

## 참고 문서

- **공통 스키마**: `libs/common/schemas/`
- **Orchestrator**: `apps/orchestrator/`
- **프로젝트 가이드**: `CLAUDE.md`
