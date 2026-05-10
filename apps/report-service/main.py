"""
Report Service - 통합 버전

Reporter 통합 - 정책 리포트 생성
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "libs"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
import os
from common import get_llm_gateway, get_storage_gateway, LLMGateway, StorageGateway

app = FastAPI(title="Agent T - Report Service", description="Reporter 통합 - 정책 리포트 생성", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

_llm_gateway: Optional[LLMGateway] = None
_storage_gateway: Optional[StorageGateway] = None

def get_llm() -> LLMGateway:
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = get_llm_gateway()
    return _llm_gateway

def get_storage() -> StorageGateway:
    global _storage_gateway
    if _storage_gateway is None:
        _storage_gateway = get_storage_gateway()
    return _storage_gateway

class ReportGenerateRequest(BaseModel):
    experiment_id: str; scenario_id: str; analysis_id: str; kpis: Dict[str, Any]; format: str = "markdown"
class ReportGenerateResponse(BaseModel):
    success: bool; experiment_id: str; report_id: str; status: str; report_uri: Optional[str] = None; timestamp: str
class ReportGetResponse(BaseModel):
    report_id: str; status: str; content: str; format: str; metadata: Dict[str, Any]; timestamp: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "report-service", "timestamp": datetime.utcnow().isoformat(), "version": "0.3.0"}

@app.get("/ready")
async def readiness_check():
    try:
        llm = get_llm()
        storage = get_storage()
        return {"status": "ready", "service": "report-service", "dependencies": {"llm_gateway": llm.provider_name, "storage_gateway": storage.provider_name}}
    except Exception as e:
        return {"status": "degraded", "service": "report-service", "error": str(e)}

@app.get("/")
async def root():
    try:
        llm = get_llm()
        storage = get_storage()
        gateways = {"llm": llm.provider_name, "storage": storage.provider_name}
    except Exception as e:
        gateways = {"error": str(e)}

    return {"service": "report-service", "description": "Reporter 통합 - 정책 리포트 생성", "version": "0.3.0", "modules": {"reporter": "Markdown/PDF/HTML 리포트 생성"}, "endpoints": {"/report/generate": "POST", "/report/{id}": "GET"}, "gateways": gateways}

@app.post("/report/generate", response_model=ReportGenerateResponse)
async def generate_report(request: ReportGenerateRequest):
    try:
        llm = get_llm()
        storage = get_storage()

        system_prompt = """당신은 교통 시뮬레이션 분석 리포트 작성 전문가입니다.
KPI 데이터를 바탕으로 정책 의사결정자를 위한 리포트를 작성하세요.

리포트 구조:
1. 요약 (Executive Summary)
2. 주요 지표 (Key Performance Indicators)
3. 분석 결과 (Analysis Results)
4. 정책 제안 (Policy Recommendations)
5. 결론 (Conclusion)

Markdown 포맷으로 작성하세요."""

        prompt = f"""실험 ID: {request.experiment_id}
시나리오 ID: {request.scenario_id}
분석 ID: {request.analysis_id}

KPI 데이터:
{request.kpis}

위 데이터를 바탕으로 정책 리포트를 작성하세요."""

        response = await llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000,
            prompt_version="report-generate-v1.0"
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        report_id = f"report-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        report_content = response.content.encode()
        report_uri = await storage.upload(
            f"reports/{request.experiment_id}/{report_id}.md",
            report_content,
            content_type="text/markdown",
            metadata={"experiment_id": request.experiment_id, "analysis_id": request.analysis_id, "model_id": response.model_id}
        )

        return ReportGenerateResponse(success=True, experiment_id=request.experiment_id, report_id=report_id, status="completed", report_uri=report_uri, timestamp=datetime.utcnow().isoformat())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/{report_id}", response_model=ReportGetResponse)
async def get_report(report_id: str):
    content = f"""# 교통 시뮬레이션 분석 리포트

## 요약
본 리포트는 {report_id} 실험의 결과를 분석한 내용입니다.

## 주요 지표
- 평균 통행 시간: 420.5초
- 평균 대기 시간: 45.2초
- 처리량: 850대/시간

## 정책 제안
1. 신호등 최적화 검토
2. 차선 운영 개선
3. 혼잡 시간대 교통 분산"""

    metadata = {"generated_at": datetime.utcnow().isoformat(), "version": "0.3.0"}
    return ReportGetResponse(report_id=report_id, status="completed", content=content, format="markdown", metadata=metadata, timestamp=datetime.utcnow().isoformat())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
