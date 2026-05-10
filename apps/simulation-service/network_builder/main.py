"""
Network Builder Service

NetworkBuildRequest로부터 SUMO 도로망 생성
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
from common.schemas import NetworkBuildRequest, NetworkArtifact

from .services.network_builder_service import NetworkBuilderService


app = FastAPI(
    title="Network Builder Service",
    description="NetworkBuildRequest로부터 SUMO 도로망(.net.xml) 생성",
    version="0.1.0"
)


# Global 서비스 인스턴스
network_builder: Optional[NetworkBuilderService] = None


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global network_builder

    # Storage Gateway 초기화
    storage_gateway = get_storage_gateway()

    # Network Builder Service 초기화
    network_builder = NetworkBuilderService(storage_gateway=storage_gateway)

    print("✓ Network Builder Service 시작 완료")
    print(f"  - Storage Gateway: {storage_gateway.__class__.__name__}")
    print(f"  - Network Builder 초기화 완료")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "network-builder",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@app.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    if network_builder is None:
        raise HTTPException(status_code=503, detail="Network builder not initialized")

    return {
        "status": "ready",
        "service": "network-builder",
        "timestamp": datetime.utcnow().isoformat()
    }


class BuildNetworkRequest(BaseModel):
    """도로망 빌드 요청"""

    network_build_request: dict = Field(
        ...,
        description="NetworkBuildRequest JSON"
    )


@app.post("/network/build", response_model=dict)
async def build_network(request: BuildNetworkRequest):
    """
    도로망 빌드

    ## 흐름

    1. NetworkBuildRequest 검증
    2. NetworkProvider 선택 (Toy / OSM)
    3. 도로망 데이터 생성 (NetworkData)
    4. 수정사항 적용 (modifications)
       - lane_change: 차로 수 변경
       - speed_change: 속도 제한 변경
       - traffic_light: 신호등 타이밍 변경 (placeholder)
    5. SUMO .net.xml 생성
    6. StorageGateway로 저장
    7. NetworkArtifact 반환

    ## 지원 소스 타입

    - **toy**: 간단한 그리드 도로망 (테스트용)
    - **osm**: OpenStreetMap (향후 구현)
    - **bbox**: OSM bbox 범위 (향후 구현)

    ## 지원 수정사항

    - **lane_change**: 차로 수 변경 (strategy: increase_major_roads, increase_all)
    - **speed_change**: 속도 제한 변경 (speed_multiplier)
    - **traffic_light**: 신호등 타이밍 (cycle_seconds, green_time_ratio) - placeholder
    """
    if network_builder is None:
        raise HTTPException(status_code=503, detail="Network builder not initialized")

    try:
        # NetworkBuildRequest 검증
        network_req_obj = NetworkBuildRequest(**request.network_build_request)

        # 도로망 빌드
        artifact = await network_builder.build_network(
            request=request.network_build_request
        )

        return artifact

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "network-builder",
        "version": "0.1.0",
        "description": "NetworkBuildRequest로부터 SUMO 도로망(.net.xml) 생성",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "build": "/network/build",
        },
        "supported_source_types": [
            {
                "type": "toy",
                "description": "간단한 그리드 도로망 (테스트용)",
                "status": "implemented",
            },
            {
                "type": "osm",
                "description": "OpenStreetMap 데이터",
                "status": "placeholder",
            },
            {
                "type": "bbox",
                "description": "OSM bbox 범위",
                "status": "placeholder",
            },
        ],
        "supported_modifications": [
            {
                "type": "lane_change",
                "description": "차로 수 변경",
                "parameters": ["strategy", "lane_delta"],
                "status": "implemented",
            },
            {
                "type": "speed_change",
                "description": "속도 제한 변경",
                "parameters": ["strategy", "speed_multiplier"],
                "status": "implemented",
            },
            {
                "type": "traffic_light",
                "description": "신호등 타이밍 변경",
                "parameters": ["cycle_seconds", "green_time_ratio"],
                "status": "placeholder",
            },
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
