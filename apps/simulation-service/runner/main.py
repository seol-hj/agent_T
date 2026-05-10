"""
Simulator Runner Service

SUMO 시뮬레이션 실행 서비스
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sys
import os

# 공통 라이브러리 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

from common import get_storage_gateway
from common.schemas import SimulationRunRequest, SimulationRunArtifact

from .executors.dry_run_executor import DryRunSumoExecutor
from .executors.local_executor import LocalSumoExecutor
from .executors.kubernetes_executor import KubernetesJobExecutor
from .services.simulation_runner_service import SimulationRunnerService


app = FastAPI(
    title="Simulator Runner Service",
    description="SUMO 시뮬레이션 실행 및 결과 수집",
    version="0.1.0"
)


# Global 서비스 인스턴스
simulation_runner: Optional[SimulationRunnerService] = None


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global simulation_runner

    # Storage Gateway 초기화
    storage_gateway = get_storage_gateway()

    # Executor 선택 (환경 변수로 제어)
    executor_type = os.getenv("SUMO_EXECUTOR_TYPE", "dry_run")

    if executor_type == "dry_run":
        executor = DryRunSumoExecutor(simulate_delay=True)
    elif executor_type == "local":
        executor = LocalSumoExecutor(
            sumo_binary=os.getenv("SUMO_BINARY", "sumo"),
            timeout_seconds=int(os.getenv("SUMO_TIMEOUT", "300")),
        )
    elif executor_type == "kubernetes":
        executor = KubernetesJobExecutor(
            namespace=os.getenv("K8S_NAMESPACE", "agent-t"),
            image=os.getenv("K8S_JOB_IMAGE", "simulation-runner:latest"),
            image_pull_policy=os.getenv("K8S_IMAGE_PULL_POLICY", "Always"),
            timeout_seconds=int(os.getenv("K8S_JOB_TIMEOUT", "600")),
            poll_interval_seconds=int(os.getenv("K8S_POLL_INTERVAL", "5")),
            storage_gateway_url=os.getenv("STORAGE_GATEWAY_URL", "http://storage-gateway:9002"),
            in_cluster=os.getenv("K8S_IN_CLUSTER", "true").lower() == "true",
        )
    else:
        raise ValueError(f"Unknown executor type: {executor_type}")

    # 환경 검증
    is_valid, message = executor.validate_environment()
    if not is_valid:
        print(f"⚠️  Executor validation warning: {message}")
    else:
        print(f"✓ Executor validation: {message}")

    # Simulation Runner Service 초기화
    simulation_runner = SimulationRunnerService(
        storage_gateway=storage_gateway,
        executor=executor,
    )

    print("✓ Simulator Runner Service 시작 완료")
    print(f"  - Storage Gateway: {storage_gateway.__class__.__name__}")
    print(f"  - Executor: {executor.__class__.__name__}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "simulator-runner",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@app.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    if simulation_runner is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialized")

    return {
        "status": "ready",
        "service": "simulator-runner",
        "timestamp": datetime.utcnow().isoformat()
    }


class RunSimulationRequest(BaseModel):
    """시뮬레이션 실행 요청"""

    simulation_run_request: dict = Field(
        ...,
        description="SimulationRunRequest JSON"
    )


@app.post("/simulation/run", response_model=dict)
async def run_simulation(request: RunSimulationRequest):
    """
    SUMO 시뮬레이션 실행

    ## 흐름

    1. SimulationRunRequest 검증
    2. NetworkArtifact 다운로드
    3. DemandArtifact 다운로드
    4. .sumocfg 생성
    5. SUMO 실행 (Executor 선택)
    6. 출력 파일 수집 (tripinfo, summary, queue, emission)
    7. StorageGateway로 업로드
    8. SimulationRunArtifact 반환

    ## Executor 타입

    - **dry_run**: 모의 실행 (테스트용, 더미 출력 생성)
    - **local**: 로컬 SUMO 실행 (subprocess)
    - **k8s**: Kubernetes Job 실행 (향후 구현)

    ## 출력 파일

    - **tripinfo.xml**: 개별 차량 통행 정보
    - **summary.xml**: 타임스텝별 요약 통계
    - **queue.xml**: 대기열 정보
    - **emission.xml**: 배출량 정보
    """
    if simulation_runner is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialized")

    try:
        # SimulationRunRequest 검증
        sim_req_obj = SimulationRunRequest(**request.simulation_run_request)

        # 시뮬레이션 실행
        artifact = await simulation_runner.run_simulation(
            request=request.simulation_run_request,
        )

        return artifact

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    executor_type = os.getenv("SUMO_EXECUTOR", "dry_run")

    return {
        "service": "simulator-runner",
        "version": "0.1.0",
        "description": "SUMO 시뮬레이션 실행 및 결과 수집",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "run": "/simulation/run",
        },
        "executor_type": executor_type,
        "supported_executors": [
            {
                "type": "dry_run",
                "description": "모의 실행 (테스트용)",
                "status": "implemented",
            },
            {
                "type": "local",
                "description": "로컬 SUMO 실행",
                "status": "implemented",
            },
            {
                "type": "k8s",
                "description": "Kubernetes Job 실행",
                "status": "placeholder",
            },
        ],
        "output_files": [
            "tripinfo.xml",
            "summary.xml",
            "queue.xml",
            "emission.xml",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
