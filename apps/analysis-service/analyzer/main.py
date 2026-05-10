"""
Analyzer Service

시뮬레이션 결과 분석 및 KPI 추출
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
from common.schemas import AnalysisRequest, AnalysisResult

from .services.analysis_service import AnalysisService


app = FastAPI(
    title="Analyzer Service",
    description="SUMO 시뮬레이션 결과 분석 및 KPI 추출",
    version="0.1.0"
)


# Global 서비스 인스턴스
analyzer: Optional[AnalysisService] = None


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global analyzer

    # Storage Gateway 초기화
    storage_gateway = get_storage_gateway()

    # Analysis Service 초기화
    analyzer = AnalysisService(storage_gateway=storage_gateway)

    print("✓ Analyzer Service 시작 완료")
    print(f"  - Storage Gateway: {storage_gateway.__class__.__name__}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "analyzer",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@app.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    return {
        "status": "ready",
        "service": "analyzer",
        "timestamp": datetime.utcnow().isoformat()
    }


class AnalyzeRequest(BaseModel):
    """분석 요청"""

    analysis_request: dict = Field(
        ...,
        description="AnalysisRequest JSON"
    )


@app.post("/analysis/run", response_model=dict)
async def run_analysis(request: AnalyzeRequest):
    """
    시뮬레이션 결과 분석

    ## 흐름

    1. AnalysisRequest 검증
    2. Baseline 시뮬레이션 결과 다운로드
    3. Alternative 시뮬레이션 결과 다운로드
    4. SUMO XML 파싱 (tripinfo, summary, queue, emission)
    5. KPI 추출
    6. Baseline vs Alternative 비교
    7. 개선율 계산
    8. AnalysisResult 반환

    ## 추출 KPI

    - **average_travel_time**: 평균 통행 시간 (초)
    - **average_waiting_time**: 평균 대기 시간 (초)
    - **average_speed**: 평균 속도 (m/s)
    - **average_queue_length**: 평균 대기열 길이 (m)
    - **completed_vehicle_count**: 완료 차량 수
    - **total_co2**: 총 CO2 배출량 (mg)
    - **total_fuel**: 총 연료 소비 (ml)

    ## 개선율

    각 KPI의 변화율을 백분율로 계산. 양수는 개선, 음수는 악화.
    """
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        # AnalysisRequest 검증
        analysis_req_obj = AnalysisRequest(**request.analysis_request)

        # 분석 실행
        result = await analyzer.analyze(
            request=request.analysis_request,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "analyzer",
        "version": "0.1.0",
        "description": "SUMO 시뮬레이션 결과 분석 및 KPI 추출",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "analyze": "/analysis/run",
        },
        "supported_kpis": [
            {
                "name": "average_travel_time",
                "unit": "seconds",
                "description": "평균 통행 시간",
            },
            {
                "name": "average_waiting_time",
                "unit": "seconds",
                "description": "평균 대기 시간",
            },
            {
                "name": "average_speed",
                "unit": "m/s",
                "description": "평균 속도",
            },
            {
                "name": "average_queue_length",
                "unit": "meters",
                "description": "평균 대기열 길이",
            },
            {
                "name": "completed_vehicle_count",
                "unit": "count",
                "description": "완료 차량 수",
            },
            {
                "name": "total_co2",
                "unit": "mg",
                "description": "총 CO2 배출량",
            },
            {
                "name": "total_fuel",
                "unit": "ml",
                "description": "총 연료 소비",
            },
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
