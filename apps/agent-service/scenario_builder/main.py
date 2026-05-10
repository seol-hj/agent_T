"""
Scenario Builder Service

ExperimentSpec으로부터 ScenarioPlan 및 빌드 요청 생성
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sys
import os

# 공통 라이브러리 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

from common.schemas import ExperimentSpec

from .services.scenario_generator import ScenarioGenerator
from .models.scenario_output import ScenarioBuilderOutput


app = FastAPI(
    title="Scenario Builder Service",
    description="ExperimentSpec으로부터 시나리오 계획 및 빌드 요청 생성",
    version="0.1.0"
)


# Global 서비스 인스턴스
scenario_generator: Optional[ScenarioGenerator] = None


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global scenario_generator

    # Scenario Generator 초기화
    scenario_generator = ScenarioGenerator()

    print("✓ Scenario Builder Service 시작 완료")
    print(f"  - Scenario Generator 초기화 완료")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "scenario-builder",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@app.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    if scenario_generator is None:
        raise HTTPException(status_code=503, detail="Scenario generator not initialized")

    return {
        "status": "ready",
        "service": "scenario-builder",
        "timestamp": datetime.utcnow().isoformat()
    }


class BuildScenariosRequest(BaseModel):
    """시나리오 빌드 요청"""

    experiment_spec: dict = Field(
        ...,
        description="실험 명세 (ExperimentSpec JSON)"
    )

    request_type: str = Field(
        ...,
        description="요청 타입",
        examples=["demand_increase", "lane_change", "signal_timing_change"]
    )


@app.post("/scenario-builder/build", response_model=ScenarioBuilderOutput)
async def build_scenarios(request: BuildScenariosRequest):
    """
    ExperimentSpec으로부터 시나리오 생성

    ## 흐름

    1. ExperimentSpec 검증
    2. Baseline 시나리오 생성 (현재 상태)
    3. Alternative 시나리오 생성 (요청 타입별)
    4. ScenarioPlan 생성
    5. NetworkBuildRequest 생성 (각 변형당)
    6. DemandBuildRequest 생성 (각 변형당)

    ## 출력

    - **scenario_plan**: ScenarioPlan (Baseline + Alternatives)
    - **network_requests**: NetworkBuildRequest 목록 (변형당 1개)
    - **demand_requests**: DemandBuildRequest 목록 (변형당 1개)

    ## 지원 요청 타입

    - **demand_increase**: 교통량 증가 시나리오 (기본 20% 증가)
    - **lane_change**: 차로 변경 시나리오 (주요 도로 +1 차로)
    - **signal_timing_change**: 신호 타이밍 변경 (최적화된 신호 주기)
    """
    if scenario_generator is None:
        raise HTTPException(status_code=503, detail="Scenario generator not initialized")

    # 지원 요청 타입 확인
    supported_types = ["demand_increase", "lane_change", "signal_timing_change"]
    if request.request_type not in supported_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported request type: {request.request_type}. "
                   f"Supported: {', '.join(supported_types)}"
        )

    try:
        # ExperimentSpec 검증
        experiment_spec_obj = ExperimentSpec(**request.experiment_spec)

        # 시나리오 생성
        output = scenario_generator.generate_scenarios(
            experiment_spec=request.experiment_spec,
            request_type=request.request_type,
        )

        return output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "scenario-builder",
        "version": "0.1.0",
        "description": "ExperimentSpec으로부터 시나리오 계획 및 빌드 요청 생성",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "build": "/scenario-builder/build",
        },
        "supported_request_types": [
            {
                "type": "demand_increase",
                "description": "교통량 증가 시나리오 (기본 20% 증가)",
            },
            {
                "type": "lane_change",
                "description": "차로 변경 시나리오 (주요 도로 +1 차로)",
            },
            {
                "type": "signal_timing_change",
                "description": "신호 타이밍 변경 시나리오 (최적화된 신호 주기)",
            },
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
