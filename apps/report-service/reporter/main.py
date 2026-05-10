"""
Reporter Service

정책적 리포트 생성 서비스
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sys
import os

# 공통 라이브러리 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

from common import get_storage_gateway, get_llm_gateway
from common.schemas import ReportRequest, ReportArtifact

from .reporters.template_reporter import TemplateReporter
from .reporters.llm_reporter import LLMReporter
from .services.report_service import ReportService


app = FastAPI(
    title="Reporter Service",
    description="교통 시뮬레이션 분석 결과를 정책적 리포트로 생성",
    version="0.1.0"
)


# Global 서비스 인스턴스
template_report_service: Optional[ReportService] = None
llm_report_service: Optional[ReportService] = None


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global template_report_service, llm_report_service

    # Storage Gateway 초기화
    storage_gateway = get_storage_gateway()

    # Template Reporter 초기화
    template_reporter = TemplateReporter()
    template_report_service = ReportService(
        storage_gateway=storage_gateway,
        reporter=template_reporter,
    )

    # LLM Reporter 초기화 (선택적)
    try:
        llm_gateway = get_llm_gateway()
        llm_reporter = LLMReporter(llm_gateway=llm_gateway)
        llm_report_service = ReportService(
            storage_gateway=storage_gateway,
            reporter=llm_reporter,
        )
        print("✓ LLM Reporter 초기화 완료")
    except Exception as e:
        print(f"⚠️  LLM Reporter 초기화 실패: {e}")
        print("  Template Reporter만 사용 가능합니다.")

    print("✓ Reporter Service 시작 완료")
    print(f"  - Storage Gateway: {storage_gateway.__class__.__name__}")
    print(f"  - Template Reporter: 사용 가능")
    print(f"  - LLM Reporter: {'사용 가능' if llm_report_service else '사용 불가'}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "reporter",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@app.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    if template_report_service is None:
        raise HTTPException(status_code=503, detail="Reporter not initialized")

    return {
        "status": "ready",
        "service": "reporter",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_available": llm_report_service is not None,
    }


class GenerateReportRequest(BaseModel):
    """리포트 생성 요청"""

    report_request: dict = Field(
        ...,
        description="ReportRequest JSON"
    )

    reporter_type: str = Field(
        default="template",
        description="Reporter 타입 (template / llm)"
    )


@app.post("/report/generate", response_model=dict)
async def generate_report(request: GenerateReportRequest):
    """
    리포트 생성

    ## 흐름

    1. ReportRequest 검증
    2. Reporter 선택 (Template / LLM)
    3. 리포트 생성 (Markdown)
    4. PDF 생성 (향후)
    5. StorageGateway로 업로드
    6. ReportArtifact 반환

    ## Reporter 타입

    - **template**: 템플릿 기반 리포트 (빠름, LLM 불필요)
    - **llm**: LLM 기반 정책적 해석 리포트 (느림, LLM 필요)

    ## 리포트 구성

    1. 요약
    2. 사용자 요청
    3. 실험 조건
    4. 기준 시나리오 결과
    5. 대안 시나리오 결과
    6. 개선율
    7. 정책적 해석
    8. 제한사항
    9. 후속 검토 사항
    """
    # Reporter 선택
    if request.reporter_type == "llm":
        if llm_report_service is None:
            raise HTTPException(
                status_code=503,
                detail="LLM Reporter is not available. Use 'template' reporter instead."
            )
        report_service = llm_report_service
    elif request.reporter_type == "template":
        if template_report_service is None:
            raise HTTPException(status_code=503, detail="Reporter not initialized")
        report_service = template_report_service
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reporter_type: {request.reporter_type}. Use 'template' or 'llm'."
        )

    try:
        # ReportRequest 검증
        report_req_obj = ReportRequest(**request.report_request)

        # 리포트 생성
        artifact = await report_service.generate_report(
            request=request.report_request,
        )

        return artifact

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "reporter",
        "version": "0.1.0",
        "description": "교통 시뮬레이션 분석 결과를 정책적 리포트로 생성",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "generate": "/report/generate",
        },
        "reporter_types": [
            {
                "type": "template",
                "description": "템플릿 기반 리포트",
                "status": "available",
                "requires_llm": False,
            },
            {
                "type": "llm",
                "description": "LLM 기반 정책적 해석 리포트",
                "status": "available" if llm_report_service else "unavailable",
                "requires_llm": True,
            },
        ],
        "report_sections": [
            "요약",
            "사용자 요청",
            "실험 조건",
            "기준 시나리오 결과",
            "대안 시나리오 결과",
            "개선율",
            "정책적 해석",
            "제한사항",
            "후속 검토 사항",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
