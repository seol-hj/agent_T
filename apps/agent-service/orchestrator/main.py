"""
Orchestrator Service

전체 흐름 제어 및 Agent 호출 라우팅
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import os
import sys

# 공통 라이브러리 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

from common import get_llm_gateway
from common.schemas import UserRequest

from .services.parser_service import ParserService, AgentLogger
from .models.parse_response import ParseResponse, RAGContext


app = FastAPI(
    title="Orchestrator Service",
    description="AI Agent T 플랫폼 오케스트레이터",
    version="0.1.0"
)


# Global 서비스 인스턴스
parser_service: Optional[ParserService] = None
agent_logger: Optional[AgentLogger] = None


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global parser_service, agent_logger

    # LLM Gateway 초기화
    llm_gateway = get_llm_gateway()

    # Parser Service 초기화
    parser_service = ParserService(llm_gateway=llm_gateway, max_retries=3)

    # Agent Logger 초기화
    agent_logger = AgentLogger()

    print("✓ Orchestrator Service 시작 완료")
    print(f"  - LLM Gateway: {llm_gateway.__class__.__name__}")
    print(f"  - Parser Service 초기화 완료")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }


@app.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    if parser_service is None:
        raise HTTPException(status_code=503, detail="Parser service not initialized")

    return {
        "status": "ready",
        "service": "orchestrator",
        "timestamp": datetime.utcnow().isoformat()
    }


class ParseRequest(BaseModel):
    """자연어 파싱 요청"""

    user_input: str = Field(
        ...,
        description="사용자 자연어 입력",
        examples=["서울 강남구 출퇴근 시간대 교통량을 분석하고 신호등 최적화 효과를 비교하고 싶습니다"]
    )

    user_id: str = Field(
        default="anonymous",
        description="사용자 ID"
    )

    rag_contexts: Optional[list[RAGContext]] = Field(
        default=None,
        description="RAG 컨텍스트 목록 (Optional)"
    )


@app.post("/orchestrator/parse", response_model=ParseResponse)
async def parse_user_request(request: ParseRequest):
    """
    사용자 자연어 입력을 ExperimentSpec으로 변환

    ## 흐름

    1. UserRequest 생성
    2. RAG 컨텍스트 주입 (Optional)
    3. LLM을 통해 ExperimentSpec 생성
    4. Pydantic 검증 (재시도 로직 포함)
    5. missing_fields 탐지 시 보완 질문 생성
    6. AgentLog 저장

    ## 응답

    - **status="success"**: ExperimentSpec 생성 완료
    - **status="needs_clarification"**: 추가 정보 필요 (missing_fields + clarification_question)
    - **status="error"**: 오류 발생
    """
    if parser_service is None:
        raise HTTPException(status_code=503, detail="Parser service not initialized")

    # UserRequest 생성
    user_request = UserRequest(
        request_id=f"req-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        user_id=request.user_id,
        raw_input=request.user_input,
        language="ko",
    )

    # 로그: 요청 시작
    await agent_logger.log(
        level="info",
        agent_name="orchestrator",
        message="자연어 파싱 시작",
        request_id=user_request.request_id,
        context={
            "user_id": request.user_id,
            "input_length": len(request.user_input),
            "has_rag_context": bool(request.rag_contexts),
        },
    )

    try:
        # Parser Service 호출
        parse_response = await parser_service.parse_request(
            user_input=request.user_input,
            request_id=user_request.request_id,
            rag_contexts=request.rag_contexts,
        )

        # 로그: 파싱 완료
        await agent_logger.log(
            level="info" if parse_response.status != "error" else "error",
            agent_name="orchestrator",
            message=f"파싱 완료: {parse_response.status}",
            request_id=user_request.request_id,
            context={
                "status": parse_response.status,
                "request_type": parse_response.request_type,
                "confidence_score": parse_response.confidence_score,
                "processing_time_ms": parse_response.processing_time_ms,
                "has_missing_fields": bool(parse_response.missing_fields),
            },
            llm_metadata=parse_response.llm_metadata,
            error_details={"error_message": parse_response.error_message} if parse_response.error_message else None,
        )

        return parse_response

    except Exception as e:
        # 로그: 오류
        await agent_logger.log(
            level="error",
            agent_name="orchestrator",
            message="파싱 중 예외 발생",
            request_id=user_request.request_id,
            error_details={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orchestrator/logs")
async def get_logs(limit: int = 50):
    """
    최근 로그 조회 (디버깅용)

    Args:
        limit: 조회할 로그 개수 (기본 50)

    Returns:
        최근 로그 목록
    """
    if agent_logger is None:
        raise HTTPException(status_code=503, detail="Logger not initialized")

    return {
        "logs": agent_logger.logs[-limit:],
        "total": len(agent_logger.logs),
    }


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "orchestrator",
        "version": "0.1.0",
        "description": "AI Agent T 플랫폼 오케스트레이터",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "parse": "/orchestrator/parse",
            "logs": "/orchestrator/logs",
        },
        "supported_request_types": [
            "demand_increase",
            "lane_change",
            "signal_timing_change",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
