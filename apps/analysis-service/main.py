"""
Analysis Service - 통합 버전 (실제 KPI 추출)

Analyzer 통합 - 시뮬레이션 결과 분석 및 KPI 추출
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "libs"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
import os
from common import get_storage_gateway, StorageGateway

# KPI Extractor
from analyzer.kpi_extractor import KPIExtractor

app = FastAPI(
    title="Agent T - Analysis Service",
    description="Analyzer 통합 - KPI 분석 (실제 추출)",
    version="0.4.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Gateway 싱글톤
_storage_gateway: Optional[StorageGateway] = None

def get_storage() -> StorageGateway:
    global _storage_gateway
    if _storage_gateway is None:
        _storage_gateway = get_storage_gateway()
    return _storage_gateway

# Request/Response Models
class AnalysisRunRequest(BaseModel):
    experiment_id: str
    scenario_id: str
    simulation_id: str
    tripinfo_uri: str
    summary_uri: str

class AnalysisRunResponse(BaseModel):
    success: bool
    experiment_id: str
    scenario_id: str
    analysis_id: str
    status: str
    kpis: Optional[Dict[str, Any]] = None
    kpi_report: Optional[str] = None
    kpi_file_uri: Optional[str] = None
    timestamp: str

class AnalysisResultsResponse(BaseModel):
    analysis_id: str
    status: str
    kpis: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str


# Health & Info Endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "analysis-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.4.0"
    }

@app.get("/ready")
async def readiness_check():
    storage = get_storage()
    return {
        "status": "ready",
        "service": "analysis-service",
        "dependencies": {
            "storage_gateway": storage.provider_name,
        }
    }

@app.get("/")
async def root():
    storage = get_storage()
    return {
        "service": "analysis-service",
        "description": "Analyzer 통합 - KPI 분석 (실제 추출)",
        "version": "0.4.0",
        "modules": {
            "analyzer": "KPI 추출 및 통계 분석 (tripinfo.xml, summary.xml 파싱)"
        },
        "endpoints": {
            "/analysis/run": "POST - KPI 추출 실행",
            "/analysis/results/{id}": "GET - KPI 조회"
        },
        "gateways": {
            "storage": storage.provider_name
        }
    }


# Analysis Endpoint
@app.post("/analysis/run", response_model=AnalysisRunResponse)
async def run_analysis(request: AnalysisRunRequest):
    """
    SUMO 시뮬레이션 결과 파일에서 KPI 추출

    tripinfo.xml과 summary.xml을 파싱하여 실제 KPI 계산
    """
    storage = get_storage()
    analysis_id = f"analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    try:
        # 1. S3에서 시뮬레이션 결과 파일 다운로드
        tripinfo_content = await storage.download(request.tripinfo_uri)
        summary_content = await storage.download(request.summary_uri)

        # 2. KPI Extractor로 KPI 추출
        extractor = KPIExtractor()
        kpis = extractor.extract_all_kpis(tripinfo_content, summary_content)

        # 3. KPI 요약 리포트 생성
        kpi_report = extractor.generate_summary_report(kpis)

        # 4. KPI JSON 저장
        kpi_json = json.dumps(kpis, indent=2, ensure_ascii=False).encode("utf-8")
        kpi_file_uri = await storage.upload(
            f"analysis/{request.experiment_id}/{analysis_id}/kpis.json",
            kpi_json,
            content_type="application/json",
            metadata={
                "experiment_id": request.experiment_id,
                "scenario_id": request.scenario_id,
                "simulation_id": request.simulation_id,
                "analysis_id": analysis_id,
            }
        )

        # 5. 리포트 저장
        report_uri = await storage.upload(
            f"analysis/{request.experiment_id}/{analysis_id}/report.md",
            kpi_report.encode("utf-8"),
            content_type="text/markdown",
            metadata={
                "experiment_id": request.experiment_id,
                "analysis_id": analysis_id,
            }
        )

        return AnalysisRunResponse(
            success=True,
            experiment_id=request.experiment_id,
            scenario_id=request.scenario_id,
            analysis_id=analysis_id,
            status="completed",
            kpis=kpis,
            kpi_report=kpi_report,
            kpi_file_uri=kpi_file_uri,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/results/{analysis_id}", response_model=AnalysisResultsResponse)
async def get_analysis_results(analysis_id: str):
    """
    분석 결과 조회 (향후 DB 연동)

    현재는 placeholder 응답
    """
    # TODO: DB에서 분석 결과 조회
    kpis = {
        "tripinfo": {
            "completed_trips": 950,
            "avg_travel_time": 420.5,
            "avg_waiting_time": 45.2,
            "avg_time_loss": 28.15,
            "avg_route_length": 5000.0,
            "avg_speed": 12.5,
        },
        "summary": {
            "total_steps": 3600,
            "total_loaded": 1000,
            "total_ended": 950,
            "avg_vehicles_running": 120.5,
            "max_vehicles_running": 250,
            "avg_mean_speed": 11.8,
        },
        "derived": {
            "completion_rate": 0.95,
            "congestion_index": 0.107,
            "avg_speed_kmh": 45.0,
            "avg_mean_speed_kmh": 42.5,
        }
    }

    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "version": "0.4.0",
        "data_source": "placeholder"
    }

    return AnalysisResultsResponse(
        analysis_id=analysis_id,
        status="completed",
        kpis=kpis,
        metadata=metadata,
        timestamp=datetime.utcnow().isoformat()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
