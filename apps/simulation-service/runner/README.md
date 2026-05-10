# Simulator Runner

SUMO 시뮬레이션 실행 서비스. `SimulationRunRequest`를 받아 SUMO를 실행하고 결과 파일을 생성한 후 `SimulationRunArtifact`를 반환한다.

## 개요

- **입력**: `SimulationRunRequest` (JSON) + `NetworkArtifact` + `DemandArtifact`
- **출력**: `SimulationRunArtifact` (JSON) + 시뮬레이션 결과 파일 (XML)
- **지원 Executor**:
  - `dry_run`: 모의 실행 (테스트용, 더미 출력 생성)
  - `local`: 로컬 SUMO 실행 (subprocess)
  - `k8s`: Kubernetes Job 실행 (향후 구현)

## 디렉토리 구조

```
simulator-runner/
├── main.py                     # FastAPI 앱
├── executors/                  # SUMO Executor 추상화
│   ├── executor.py             # Executor 인터페이스
│   ├── dry_run_executor.py     # Dry Run Executor
│   ├── local_executor.py       # Local Executor
│   └── k8s_executor.py         # K8s Executor (placeholder)
├── services/
│   ├── config_generator.py     # .sumocfg 생성기
│   ├── command_builder.py      # SUMO 명령어 빌더
│   └── simulation_runner_service.py  # 메인 실행 서비스
├── tests/
│   ├── test_config_generator.py
│   ├── test_command_builder.py
│   ├── test_dry_run_executor.py
│   └── test_api.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## 주요 컴포넌트

### 1. SumoExecutor (인터페이스)

모든 Executor가 구현해야 할 추상 클래스.

```python
class SumoExecutor(ABC):
    @abstractmethod
    async def execute(
        self,
        config_file_path: str,
        working_directory: str,
    ) -> ExecutionResult:
        pass

    @abstractmethod
    def validate_environment(self) -> tuple[bool, str]:
        pass
```

**ExecutionResult**:
```python
@dataclass
class ExecutionResult:
    success: bool
    return_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    output_files: dict[str, str]  # {output_type: file_path}
    error_message: Optional[str] = None
```

### 2. DryRunSumoExecutor

모의 실행 Executor. 실제 SUMO를 실행하지 않고 더미 출력 파일 생성.

**특징**:
- SUMO 설치 불필요
- 빠른 E2E 테스트 가능
- 실제 SUMO XML 형식과 유사한 더미 데이터 생성
- 실행 지연 시뮬레이션 옵션

**더미 출력**:
- `tripinfo.xml`: 2개 차량의 통행 정보
- `summary.xml`: 3개 타임스텝 요약
- `queue.xml`: 2개 타임스텝 대기열 정보
- `emission.xml`: 배출량 정보

### 3. LocalSumoExecutor

로컬 SUMO 실행 Executor. `subprocess`로 SUMO CLI 실행.

**요구사항**:
- SUMO 설치 필요 (`sumo` 또는 `sumo-gui` 바이너리)
- PATH에 SUMO 등록 또는 절대 경로 지정

**옵션**:
- `sumo_binary`: SUMO 바이너리 경로 (기본: `"sumo"`)
- `timeout_seconds`: 실행 타임아웃 (기본: 300초)

### 4. KubernetesJobExecutor (Placeholder)

Kubernetes Job으로 SUMO 실행 (향후 구현).

**계획**:
- Job manifest 동적 생성
- PVC 또는 S3로 입출력 파일 전달
- Job 모니터링 및 로그 수집
- 자동 정리

### 5. SumoConfigGenerator

`.sumocfg` 파일 생성.

**생성 내용**:
```xml
<?xml version="1.0" ?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <input>
    <net-file value="network.net.xml"/>
    <route-files value="routes.rou.xml"/>
  </input>
  <output>
    <tripinfo-output value="tripinfo.xml"/>
    <summary-output value="summary.xml"/>
    <queue-output value="queue.xml"/>
    <emission-output value="emission.xml"/>
  </output>
  <time>
    <begin value="0"/>
    <step-length value="1.0"/>
  </time>
  <processing>
    <collision.action value="warn"/>
    <time-to-teleport value="300"/>
  </processing>
  <report>
    <verbose value="true"/>
    <no-step-log value="false"/>
  </report>
</configuration>
```

### 6. SumoCommandBuilder

SUMO CLI 명령어 생성 (로깅 및 디버깅용).

**예시**:
```bash
sumo -c simulation.sumocfg --verbose --time-to-teleport 300
```

### 7. SimulationRunnerService

전체 실행 흐름 관리:

1. `SimulationRunRequest` 파싱
2. 임시 작업 디렉토리 생성
3. `NetworkArtifact` 다운로드 (`.net.xml`)
4. `DemandArtifact` 다운로드 (`.rou.xml`)
5. `.sumocfg` 생성
6. SUMO 실행 (Executor 선택)
7. 출력 파일 수집 및 업로드
8. 통계 계산
9. `SimulationRunArtifact` 반환
10. 임시 디렉토리 정리

## API 엔드포인트

### POST /simulation/run

시뮬레이션 실행.

**요청**:
```json
{
  "simulation_run_request": {
    "schema_version": "1.0",
    "request_id": "req-sim-001",
    "experiment_id": "exp-001",
    "variant_id": "baseline",
    "network_artifact": {
      "schema_version": "1.0",
      "artifact_id": "net-001",
      "uri": "s3://bucket/exp-001/baseline/network.net.xml",
      "file_format": "net.xml",
      "file_size_bytes": 50000
    },
    "demand_artifact": {
      "schema_version": "1.0",
      "artifact_id": "dem-001",
      "uri": "s3://bucket/exp-001/baseline/routes.rou.xml",
      "file_format": "rou.xml",
      "file_size_bytes": 12000
    },
    "simulation_settings": {
      "begin": 0,
      "end": 3600,
      "step_length": 1.0,
      "collision_action": "warn",
      "time_to_teleport": 300
    }
  }
}
```

**응답** (`SimulationRunArtifact`):
```json
{
  "schema_version": "1.0",
  "artifact_id": "sim-001-baseline",
  "request_id": "req-sim-001",
  "experiment_id": "exp-001",
  "variant_id": "baseline",
  "outputs": {
    "tripinfo": "s3://bucket/exp-001/baseline/tripinfo.xml",
    "summary": "s3://bucket/exp-001/baseline/summary.xml",
    "queue": "s3://bucket/exp-001/baseline/queue.xml",
    "emission": "s3://bucket/exp-001/baseline/emission.xml"
  },
  "statistics": {
    "tripinfo_size_bytes": 15420,
    "summary_size_bytes": 8230,
    "queue_size_bytes": 5120,
    "emission_size_bytes": 12890
  },
  "status": "completed",
  "created_at": "2026-05-07T12:00:00",
  "generated_by": "simulator-runner-v0.1.0",
  "execution_time_ms": 2500.5
}
```

**실패 응답** (`status: "failed"`):
```json
{
  "schema_version": "1.0",
  "artifact_id": "sim-001-baseline",
  "status": "failed",
  "error_message": "SUMO execution timed out after 300s",
  "execution_time_ms": 300000.0
}
```

### GET /health

헬스 체크.

### GET /ready

준비 상태 체크.

### GET /

서비스 정보 및 지원 Executor 목록.

## 로컬 실행

### Dry Run 모드 (SUMO 설치 불필요)

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export STORAGE_PROVIDER=local
export STORAGE_BASE_PATH=/tmp/simulations
export SUMO_EXECUTOR=dry_run
export PORT=8004

# 서비스 시작
python -m uvicorn simulator_runner.main:app --host 0.0.0.0 --port 8004 --reload
```

### Local 모드 (SUMO 설치 필요)

```bash
# SUMO 설치 (Ubuntu/Debian)
sudo apt-get install sumo sumo-tools

# 환경 변수 설정
export STORAGE_PROVIDER=local
export STORAGE_BASE_PATH=/tmp/simulations
export SUMO_EXECUTOR=local
export SUMO_BINARY=sumo
export SUMO_TIMEOUT=300
export PORT=8004

# 서비스 시작
python -m uvicorn simulator_runner.main:app --host 0.0.0.0 --port 8004 --reload
```

## Docker 실행

```bash
# 이미지 빌드
docker build -t simulator-runner:latest -f apps/simulator-runner/Dockerfile .

# Dry Run 모드
docker run -d \
  --name simulator-runner \
  -p 8004:8004 \
  -e STORAGE_PROVIDER=local \
  -e STORAGE_BASE_PATH=/app/data/simulations \
  -e SUMO_EXECUTOR=dry_run \
  simulator-runner:latest

# Local 모드 (SUMO 설치 필요)
docker run -d \
  --name simulator-runner \
  -p 8004:8004 \
  -e STORAGE_PROVIDER=local \
  -e SUMO_EXECUTOR=local \
  -v /usr/share/sumo:/usr/share/sumo \
  simulator-runner:latest
```

## 테스트

```bash
# 모든 테스트 실행
pytest apps/simulator-runner/tests/ -v

# 특정 테스트 실행
pytest apps/simulator-runner/tests/test_config_generator.py -v
pytest apps/simulator-runner/tests/test_dry_run_executor.py -v
pytest apps/simulator-runner/tests/test_api.py -v

# 비동기 테스트는 pytest-asyncio 필요
pip install pytest-asyncio

# 커버리지
pytest apps/simulator-runner/tests/ --cov=apps.simulator-runner --cov-report=html
```

## 설정

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `STORAGE_PROVIDER` | `local` | 스토리지 제공자 (`local` / `s3`) |
| `STORAGE_BASE_PATH` | `/app/data/simulations` | 로컬 저장 경로 |
| `SUMO_EXECUTOR` | `dry_run` | Executor 타입 (`dry_run` / `local` / `k8s`) |
| `SUMO_BINARY` | `sumo` | SUMO 바이너리 경로 (local mode) |
| `SUMO_TIMEOUT` | `300` | 실행 타임아웃 (초, local mode) |
| `K8S_NAMESPACE` | `agent-t` | K8s 네임스페이스 (k8s mode) |
| `PORT` | `8004` | 서비스 포트 |

### simulation_settings 옵션

| 옵션 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `begin` | float | X | 0 | 시작 시간 (초) |
| `end` | float | X | None | 종료 시간 (초, None이면 모든 차량 완료까지) |
| `step_length` | float | X | 1.0 | 타임스텝 길이 (초) |
| `collision_action` | string | X | `"warn"` | 충돌 시 동작 (`warn` / `remove` / `teleport`) |
| `time_to_teleport` | int | X | 300 | 텔레포트 시간 (초) |

## 출력 파일

### tripinfo.xml

개별 차량의 통행 정보.

**주요 속성**:
- `depart`: 출발 시간
- `arrival`: 도착 시간
- `duration`: 통행 시간
- `routeLength`: 경로 길이
- `waitingTime`: 대기 시간
- `timeLoss`: 손실 시간

### summary.xml

타임스텝별 전체 시뮬레이션 요약.

**주요 속성**:
- `loaded`: 로드된 차량 수
- `inserted`: 삽입된 차량 수
- `running`: 주행 중 차량 수
- `waiting`: 대기 중 차량 수
- `ended`: 완료된 차량 수
- `meanSpeed`: 평균 속도
- `meanWaitingTime`: 평균 대기 시간

### queue.xml

엣지별 대기열 정보.

**주요 속성**:
- `queueing_time`: 대기 시간
- `queueing_length`: 대기열 길이
- `queueing_length_ahead_of_traffic_light`: 신호등 앞 대기열

### emission.xml

차량별 배출량 정보.

**주요 속성**:
- `CO2`: 이산화탄소 (mg)
- `CO`: 일산화탄소 (mg)
- `HC`: 탄화수소 (mg)
- `NOx`: 질소산화물 (mg)
- `PMx`: 미세먼지 (mg)
- `fuel`: 연료 소비 (ml)

## 확장 가능성

### 새 Executor 추가

1. `SumoExecutor` 인터페이스 구현
2. 환경 변수로 선택 가능하도록 `main.py`에 추가
3. 테스트 작성

**예시**:
```python
class CustomExecutor(SumoExecutor):
    async def execute(self, config_file_path, working_directory) -> ExecutionResult:
        # Custom 실행 로직
        pass

    def validate_environment(self) -> tuple[bool, str]:
        # 환경 검증
        pass
```

### 출력 파일 추가

1. `SumoConfigGenerator`에 출력 파일 정의 추가
2. `SimulationRunnerService._upload_output_files()` 수정
3. 테스트 업데이트

## 제약 사항

- **초기 구현**: Dry Run 및 Local Executor만 구현
- **K8s Executor**: 아직 미구현 (placeholder)
- **GUI 모드**: `sumo-gui`는 `SumoCommandBuilder`에서 지원하지만 서비스에서는 사용하지 않음
- **타임아웃**: Local Executor는 기본 300초 타임아웃 (설정 가능)

## 다음 단계

1. **K8s Job Executor 구현**: 대규모 시뮬레이션을 위한 분산 실행
2. **실시간 진행 상황 모니터링**: WebSocket 또는 polling으로 진행률 제공
3. **결과 파일 파싱**: XML → 구조화된 데이터로 변환
4. **재시도 로직**: 실패 시 자동 재시도
5. **캐싱**: 동일한 입력에 대한 결과 캐싱
6. **추가 출력 파일**: FCD, trajectories, detector outputs 등

## 참고

- [SUMO Documentation](https://sumo.dlr.de/docs/)
- [SUMO Configuration](https://sumo.dlr.de/docs/sumo.html)
- [SUMO Outputs](https://sumo.dlr.de/docs/Simulation/Output/)
