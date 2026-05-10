## Network Builder Service

NetworkBuildRequest로부터 SUMO 도로망(.net.xml)을 생성하는 서비스.

## 역할

- NetworkBuildRequest 입력 → NetworkArtifact 출력
- 도로망 데이터 생성 (Toy / OSM)
- 수정사항 적용 (lane_change, speed_change, traffic_light)
- SUMO .net.xml 생성
- StorageGateway로 artifact 저장

## 핵심 기능

### 1. NetworkProvider 인터페이스

도로망 생성을 위한 추상 인터페이스:
- `generate_network()`: 도로망 데이터 생성
- `apply_modifications()`: 수정사항 적용

### 2. ToyNetworkProvider

테스트 및 데모용 간단한 그리드 도로망 생성:
- 그리드 형태 (rows x cols)
- 양방향 엣지
- 자동 연결 생성
- 신호등 생성 (내부 노드)

### 3. OSMNetworkProvider (Placeholder)

OpenStreetMap 데이터로부터 실제 도로망 생성 (향후 구현):
- Overpass API로 OSM 다운로드
- netconvert 또는 osmium으로 변환
- SUMO 네트워크 생성

### 4. SumoNetworkGenerator

NetworkData를 SUMO .net.xml 형식으로 변환:
- XML 생성 (nodes, edges, lanes, connections)
- Pretty print
- 통계 계산

### 5. 지원 수정사항

**lane_change** (차로 수 변경):
- `strategy: increase_all`: 모든 엣지
- `strategy: increase_major_roads`: 주요 도로만
- `lane_delta`: 변경할 차로 수 (+1, -1)

**speed_change** (속도 제한 변경):
- `strategy: increase_all / decrease_all`
- `speed_multiplier`: 속도 배율 (1.2 = 20% 증가)

**traffic_light** (신호등 타이밍 - Placeholder):
- `cycle_seconds`: 신호 주기 (초)
- `green_time_ratio`: 녹색 시간 비율 (0.55 = 55%)

## 아키텍처

```
┌─────────────────────────────┐
│   FastAPI Main              │
│   (main.py)                 │
└──────────┬──────────────────┘
           │
           ├─► NetworkBuilderService (services/network_builder_service.py)
           │   ├─► NetworkProvider (선택)
           │   │   ├─► ToyNetworkProvider (구현)
           │   │   └─► OSMNetworkProvider (placeholder)
           │   ├─► SumoNetworkGenerator
           │   │   └─► XML 생성
           │   └─► StorageGateway
           │       └─► .net.xml 저장
           │
           └─► Pydantic Schemas
               ├─► NetworkBuildRequest
               └─► NetworkArtifact
```

## 설치 및 실행

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
export STORAGE_PROVIDER=local
export STORAGE_BASE_PATH=/app/data/networks

# 서버 시작
python -m uvicorn apps.network-builder.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t network-builder:latest -f apps/network-builder/Dockerfile .

# 컨테이너 실행
docker run -d \
  -p 8002:8002 \
  -e STORAGE_PROVIDER=local \
  -e STORAGE_BASE_PATH=/app/data/networks \
  network-builder:latest
```

## API 엔드포인트

### POST `/network/build`

NetworkBuildRequest로부터 도로망을 생성합니다.

**요청**:
```json
{
  "network_build_request": {
    "schema_version": "1.0",
    "request_id": "netreq-001-base-001",
    "experiment_id": "exp-20260507-001",
    "variant_id": "base-001",
    "osm_source": {
      "type": "toy",
      "grid_size": [3, 3]
    },
    "network_options": {
      "default_lanes": 2,
      "default_speed": 13.89,
      "tls_guess": true
    },
    "modifications": [
      {
        "type": "lane_change",
        "strategy": "increase_all",
        "lane_delta": 1
      }
    ],
    "created_at": "2026-05-07T12:00:00Z"
  }
}
```

**응답**:
```json
{
  "schema_version": "1.0",
  "artifact_id": "net-001-base-001",
  "request_id": "netreq-001-base-001",
  "experiment_id": "exp-20260507-001",
  "variant_id": "base-001",
  "uri": "file:///app/data/networks/exp-20260507-001/base-001/network.net.xml",
  "file_format": "net.xml",
  "file_size_bytes": 5243,
  "statistics": {
    "nodes": 9,
    "edges": 24,
    "junctions": 9,
    "traffic_lights": 1,
    "total_length_km": 4.8,
    "avg_edge_length_m": 200.0
  },
  "created_at": "2026-05-07T12:00:00.123Z",
  "generated_by": "network-builder-v0.1.0"
}
```

## 테스트

```bash
# ToyNetworkProvider 테스트
pytest apps/network-builder/tests/test_toy_network_provider.py -v

# SumoNetworkGenerator 테스트
pytest apps/network-builder/tests/test_sumo_network_generator.py -v

# API 테스트
pytest apps/network-builder/tests/test_api.py -v

# 전체 테스트
pytest apps/network-builder/tests/ -v
```

### 주요 테스트 케이스

**ToyNetworkProvider** (15개):
- ✅ 기본 그리드 생성
- ✅ 사용자 정의 그리드 크기
- ✅ 노드/엣지/연결 구조 검증
- ✅ 신호등 생성/비활성화
- ✅ lane_change 적용 (all / major)
- ✅ speed_change 적용
- ✅ traffic_light 타이밍 변경
- ✅ 여러 수정사항 동시 적용
- ✅ 도로망 통계

**SumoNetworkGenerator** (10개):
- ✅ 기본 XML 생성
- ✅ 노드/엣지/lane/연결 포함
- ✅ 신호등 포함 XML
- ✅ 통계 계산
- ✅ Pretty print
- ✅ SUMO 형식 유효성

**API** (9개):
- ✅ 헬스/준비 체크
- ✅ Toy 도로망 빌드
- ✅ lane_change 포함 빌드
- ✅ speed_change 포함 빌드
- ✅ 잘못된 요청
- ✅ 서비스 미초기화

## NetworkData 구조

```python
@dataclass
class NetworkData:
    nodes: list[dict]         # 노드 목록
    edges: list[dict]         # 엣지 목록
    connections: list[dict]   # 연결 목록
    traffic_lights: Optional[list[dict]]  # 신호등 목록

# Node
{
  "id": "n_0_0",
  "x": 0.0,
  "y": 0.0,
  "type": "traffic_light"  # 또는 "priority"
}

# Edge
{
  "id": "e_0",
  "from": "n_0_0",
  "to": "n_0_1",
  "lanes": 2,
  "speed": 13.89,  # m/s
  "length": 200.0,  # m
  "priority": 1
}

# Connection
{
  "from": "e_0",
  "to": "e_1",
  "fromLane": 0,
  "toLane": 0
}

# Traffic Light
{
  "id": "tl_0",
  "junction": "n_1_1",
  "type": "static",
  "programID": "0",
  "offset": 0,
  "phases": [
    {"duration": 31, "state": "GGrrrrGGrrrr"},
    {"duration": 6, "state": "yyrrrryyrrrr"}
  ]
}
```

## SUMO .net.xml 예시

```xml
<?xml version="1.0" ?>
<net version="1.16">
  <location netOffset="0.00,0.00" convBoundary="0.00,0.00,1000.00,1000.00"/>
  
  <junction id="n_0_0" type="priority" x="0.00" y="0.00" shape=""/>
  <junction id="n_0_1" type="priority" x="200.00" y="0.00" shape=""/>
  
  <edge id="e_0" from="n_0_0" to="n_0_1" priority="1">
    <lane id="e_0_0" index="0" speed="13.89" length="200.00" shape="0.00,0.00 200.00,0.00"/>
    <lane id="e_0_1" index="1" speed="13.89" length="200.00" shape="0.00,3.20 200.00,3.20"/>
  </edge>
  
  <connection from="e_0" to="e_1" fromLane="0" toLane="0" dir="s" state="M"/>
  
  <tlLogic id="tl_0" type="static" programID="0" offset="0">
    <phase duration="31" state="GGrrrrGGrrrr"/>
    <phase duration="6" state="yyrrrryyrrrr"/>
  </tlLogic>
</net>
```

## 설계 결정 사항

### 1. Provider 추상화

**결정**: NetworkProvider 인터페이스를 통해 다양한 소스 지원.

**현재**: ToyNetworkProvider 구현, OSMNetworkProvider placeholder

**향후**: OSM 통합, 커스텀 provider

### 2. 코드가 XML 생성

**결정**: LLM이 XML을 직접 생성하지 않고, 코드가 schema 기반으로 생성.

**이유**:
- 정확성 보장
- 구조 일관성
- SUMO 형식 준수

### 3. 수정사항 추상화

**결정**: modifications를 추상적으로 전달, provider가 실제 적용.

**예**: `"increase_major_roads"` → provider가 주요 도로 선택

### 4. Toy 우선 구현

**결정**: 초기에는 ToyNetworkProvider만 완전 구현.

**이유**:
- 빠른 테스트 가능
- 전체 파이프라인 검증
- OSM 통합은 점진적 추가

## 다음 단계

1. **OSM 통합**: Overpass API + netconvert
2. **실제 신호등 프로그램**: SUMO TLS 정확한 구현
3. **더 다양한 수정사항**: 도로 추가/제거, junction 타입 변경
4. **도로망 검증**: SUMO netconvert로 검증
5. **캐싱**: 동일한 Baseline 도로망 재사용
6. **병렬 처리**: 여러 변형 동시 생성

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `STORAGE_PROVIDER` | `local` | 스토리지 제공자 (local, s3) |
| `STORAGE_BASE_PATH` | `/app/data/networks` | 로컬 저장 경로 |
| `AWS_REGION` | `ap-northeast-2` | S3 리전 (S3 사용 시) |
| `S3_BUCKET_NAME` | `agent-t-networks` | S3 버킷 이름 |
| `PORT` | `8002` | 서버 포트 |

## 참고 문서

- **공통 스키마**: `libs/common/schemas/`
- **StorageGateway**: `libs/common/gateways/storage.py`
- **Scenario Builder**: `apps/scenario-builder/`
- **SUMO 문서**: https://sumo.dlr.de/docs/Networks/SUMO_Road_Networks.html
