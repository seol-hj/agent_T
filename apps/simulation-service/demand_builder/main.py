"""
Demand Builder Service

DemandBuildRequest로부터 SUMO 교통 수요 생성
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
from common.schemas import DemandBuildRequest, DemandArtifact

from .services.demand_builder_service import DemandBuilderService


app = FastAPI(
    title="Demand Builder Service",
    description="DemandBuildRequest로부터 SUMO 교통 수요(.rou.xml) 생성",
    version="0.1.0"
)


# Global 서비스 인스턴스
demand_builder: Optional[DemandBuilderService] = None


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global demand_builder

    # Storage Gateway 초기화
    storage_gateway = get_storage_gateway()

    # Demand Builder Service 초기화
    demand_builder = DemandBuilderService(storage_gateway=storage_gateway)

    print("✓ Demand Builder Service 시작 완료")
    print(f"  - Storage Gateway: {storage_gateway.__class__.__name__}")
    print(f"  - Demand Builder 초기화 완료")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "demand-builder",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@app.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    if demand_builder is None:
        raise HTTPException(status_code=503, detail="Demand builder not initialized")

    return {
        "status": "ready",
        "service": "demand-builder",
        "timestamp": datetime.utcnow().isoformat()
    }


class BuildDemandRequest(BaseModel):
    """교통 수요 빌드 요청"""

    demand_build_request: dict = Field(
        ...,
        description="DemandBuildRequest JSON"
    )

    network_artifact: Optional[dict] = Field(
        default=None,
        description="NetworkArtifact JSON (선택적)"
    )


@app.post("/demand/build", response_model=dict)
async def build_demand(request: BuildDemandRequest):
    """
    교통 수요 빌드

    ## 흐름

    1. DemandBuildRequest 검증
    2. DemandProvider 선택 (Toy / OD Matrix)
    3. 교통 수요 데이터 생성 (DemandData)
    4. demand_multiplier 적용
    5. vehicle_type ratio 적용
    6. SUMO .rou.xml 생성
    7. StorageGateway로 저장
    8. DemandArtifact 반환

    ## 지원 Provider

    - **toy**: 무작위 OD 쌍 생성 (테스트용)
    - **od_matrix**: OD Matrix 기반 (향후 구현)

    ## 주요 설정

    - **vehicle_count**: 총 차량 수
    - **start_time**: 시작 시간 (초)
    - **end_time**: 종료 시간 (초)
    - **vehicle_types**: 차종 비율 dict (passenger, bus, truck)
    - **trip_distribution**: "random" | "uniform"
    """
    if demand_builder is None:
        raise HTTPException(status_code=503, detail="Demand builder not initialized")

    try:
        # DemandBuildRequest 검증
        demand_req_obj = DemandBuildRequest(**request.demand_build_request)

        # 교통 수요 빌드
        artifact = await demand_builder.build_demand(
            request=request.demand_build_request,
            network_artifact=request.network_artifact,
        )

        return artifact

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "demand-builder",
        "version": "0.1.0",
        "description": "DemandBuildRequest로부터 SUMO 교통 수요(.rou.xml) 생성",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "build": "/demand/build",
        },
        "supported_providers": [
            {
                "type": "toy",
                "description": "무작위 OD 쌍 생성 (테스트용)",
                "status": "implemented",
            },
            {
                "type": "od_matrix",
                "description": "OD Matrix 기반 수요 생성",
                "status": "placeholder",
            },
        ],
        "supported_vehicle_types": [
            "passenger",
            "bus",
            "truck",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
