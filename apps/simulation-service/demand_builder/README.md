# Demand Builder

교통 수요 생성 서비스. `DemandBuildRequest`를 받아 SUMO `.rou.xml` 파일을 생성하고 `DemandArtifact`를 반환한다.

## 개요

- **입력**: `DemandBuildRequest` (JSON)
- **출력**: `DemandArtifact` (JSON) + `.rou.xml` (스토리지에 저장)
- **지원 Provider**:
  - `toy`: 무작위 OD 쌍 생성 (테스트용)
  - `od_matrix`: OD Matrix 기반 (향후 구현)

## 디렉토리 구조

```
demand-builder/
├── main.py                     # FastAPI 앱
├── providers/                  # Demand Provider
│   ├── demand_provider.py      # Provider 인터페이스
│   ├── toy_demand_provider.py  # Toy Provider
│   └── od_matrix_demand_provider.py  # OD Matrix Provider (placeholder)
├── services/
│   ├── demand_builder_service.py  # 메인 빌드 서비스
│   └── route_generator.py         # SUMO .rou.xml 생성기
├── tests/
│   ├── test_toy_demand_provider.py
│   ├── test_route_generator.py
│   └── test_api.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## 주요 컴포넌트

### 1. DemandProvider (인터페이스)

모든 Provider가 구현해야 할 추상 클래스.

```python
class DemandProvider(ABC):
    @abstractmethod
    def generate_demand(
        self,
        network_data: Any,
        demand_config: dict,
    ) -> DemandData:
        pass

    @abstractmethod
    def apply_demand_multiplier(
        self,
        demand_data: DemandData,
        multiplier: float,
    ) -> DemandData:
        pass
```

### 2. ToyDemandProvider

무작위 OD 쌍 생성. 테스트 및 초기 개발용.

**기능**:
- 네트워크의 엣지에서 무작위로 출발지/목적지 선택
- 차종 비율에 따라 차량 할당
- `uniform` / `random` 출발 시간 분포
- demand_multiplier 적용

**설정**:
```json
{
  "provider_type": "toy",
  "vehicle_count": 100,
  "start_time": 0,
  "end_time": 3600,
  "vehicle_types": {
    "passenger": 0.8,
    "bus": 0.1,
    "truck": 0.1
  },
  "trip_distribution": "random",
  "demand_multiplier": 1.0
}
```

### 3. ODMatrixDemandProvider (Placeholder)

향후 실제 OD Matrix 기반 수요 생성.

### 4. RouteGenerator

`DemandData` → SUMO `.rou.xml` 변환.

**생성 내용**:
- `<vType>`: 차종 정의 (passenger, bus, truck)
- `<trip>`: 차량별 통행 (출발지, 목적지, 출발 시간)
- `<route>`: 명시적 경로 (route_edges가 있는 경우)

**예시**:
```xml
<?xml version="1.0" ?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <vType id="passenger" vClass="passenger" length="5.00" minGap="2.50" maxSpeed="30.00" accel="2.60" decel="4.50" sigma="0.50" color="1,1,0"/>
  <trip id="veh_0" type="passenger" depart="0.00" from="e_0" to="e_1"/>
  <trip id="veh_1" type="passenger" depart="10.50" from="e_1" to="e_2"/>
</routes>
```

### 5. DemandBuilderService

전체 빌드 흐름 관리:

1. `DemandBuildRequest` 파싱
2. Provider 선택 (toy / od_matrix)
3. 네트워크 데이터 준비 (Mock / 실제 NetworkArtifact)
4. 교통 수요 생성 (`DemandData`)
5. SUMO `.rou.xml` 생성
6. StorageGateway로 업로드
7. 통계 계산
8. `DemandArtifact` 반환

## API 엔드포인트

### POST /demand/build

교통 수요 빌드.

**요청**:
```json
{
  "demand_build_request": {
    "schema_version": "1.0",
    "request_id": "req-001",
    "experiment_id": "exp-001",
    "variant_id": "baseline",
    "demand_settings": {
      "provider_type": "toy",
      "vehicle_count": 100,
      "start_time": 0,
      "end_time": 3600,
      "vehicle_types": {
        "passenger": 0.8,
        "bus": 0.1,
        "truck": 0.1
      },
      "trip_distribution": "random",
      "demand_multiplier": 1.0
    }
  },
  "network_artifact": {
    "schema_version": "1.0",
    "artifact_id": "net-001",
    "uri": "s3://bucket/exp-001/baseline/network.net.xml"
  }
}
```

**응답** (`DemandArtifact`):
```json
{
  "schema_version": "1.0",
  "artifact_id": "dem-001-baseline",
  "request_id": "req-001",
  "experiment_id": "exp-001",
  "variant_id": "baseline",
  "uri": "s3://bucket/exp-001/baseline/routes.rou.xml",
  "file_format": "rou.xml",
  "file_size_bytes": 12345,
  "statistics": {
    "total_vehicles": 100,
    "vehicles_by_type": {
      "passenger": 80,
      "bus": 10,
      "truck": 10
    },
    "total_trips": 100,
    "departure_time_range": [0.0, 3600.0],
    "avg_departure_time": 1800.0
  },
  "created_at": "2026-05-07T12:00:00",
  "generated_by": "demand-builder-v0.1.0"
}
```

### GET /health

헬스 체크.

### GET /ready

준비 상태 체크.

### GET /

서비스 정보 및 지원 Provider 목록.

## 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export STORAGE_PROVIDER=local
export STORAGE_BASE_PATH=/tmp/demands
export PORT=8003

# 서비스 시작
python -m uvicorn demand_builder.main:app --host 0.0.0.0 --port 8003 --reload
```

## Docker 실행

```bash
# 이미지 빌드
docker build -t demand-builder:latest -f apps/demand-builder/Dockerfile .

# 컨테이너 실행
docker run -d \
  --name demand-builder \
  -p 8003:8003 \
  -e STORAGE_PROVIDER=local \
  -e STORAGE_BASE_PATH=/app/data/demands \
  demand-builder:latest
```

## 테스트

```bash
# 모든 테스트 실행
pytest apps/demand-builder/tests/ -v

# 특정 테스트 실행
pytest apps/demand-builder/tests/test_toy_demand_provider.py -v
pytest apps/demand-builder/tests/test_route_generator.py -v
pytest apps/demand-builder/tests/test_api.py -v

# 커버리지
pytest apps/demand-builder/tests/ --cov=apps.demand-builder --cov-report=html
```

## 설정

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `STORAGE_PROVIDER` | `local` | 스토리지 제공자 (`local` / `s3`) |
| `STORAGE_BASE_PATH` | `/app/data/demands` | 로컬 저장 경로 |
| `PORT` | `8003` | 서비스 포트 |

### demand_settings 옵션

| 옵션 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `provider_type` | string | O | `toy` | Provider 타입 (`toy` / `od_matrix`) |
| `vehicle_count` | int | O | - | 총 차량 수 |
| `start_time` | float | O | - | 시작 시간 (초) |
| `end_time` | float | O | - | 종료 시간 (초) |
| `vehicle_types` | dict | O | - | 차종 비율 (합 = 1.0) |
| `trip_distribution` | string | X | `random` | 출발 시간 분포 (`random` / `uniform`) |
| `demand_multiplier` | float | X | `1.0` | 수요 배율 |

### 지원 차종

| 차종 | vClass | 길이(m) | 최대속도(m/s) |
|------|--------|---------|---------------|
| `passenger` | passenger | 5.0 | 30.0 |
| `bus` | bus | 12.0 | 25.0 |
| `truck` | truck | 8.0 | 20.0 |

## 확장 가능성

### 새 Provider 추가

1. `DemandProvider` 인터페이스 구현
2. `DemandBuilderService.providers`에 등록
3. 테스트 작성

**예시**:
```python
class CustomDemandProvider(DemandProvider):
    def generate_demand(self, network_data, demand_config) -> DemandData:
        # Custom 로직
        pass

    def apply_demand_multiplier(self, demand_data, multiplier) -> DemandData:
        # Multiplier 적용
        pass
```

## 제약 사항

- **초기 구현**: Mock 네트워크 데이터 사용 (8개 엣지 그리드)
- **OD Matrix Provider**: 아직 미구현 (placeholder)
- **경로 계산**: SUMO에 위임 (`<trip>` 요소 사용)
- **시간 분포**: `uniform` / `random`만 지원

## 다음 단계

1. **실제 네트워크 통합**: `NetworkArtifact`에서 `.net.xml` 파싱
2. **OD Matrix Provider**: 실제 OD 데이터 기반 수요 생성
3. **경로 사전 계산**: Dijkstra 등으로 경로 계산 후 `<route>` 사용
4. **시간 분포 확장**: 첨두/비첨두 시간대, Poisson 분포 등
5. **차종 확장**: 택시, 이륜차, 긴급차량 등
6. **출발지/목적지 가중치**: 특정 존(zone) 중심 OD 생성

## 참고

- [SUMO Route 파일 형식](https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html)
- [SUMO Vehicle Types](https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html#vehicle_types)
