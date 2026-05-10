"""
Agent Service - 통합 버전

AI Agent + Orchestrator + Scenario Builder 통합
"""

import sys
from pathlib import Path

# Common library를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "libs"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

# Gateway imports
from common import (
    get_llm_gateway,
    get_storage_gateway,
    LLMGateway,
    StorageGateway,
)

app = FastAPI(
    title="Agent T - Agent Service",
    description="AI Agent + Orchestrator + Scenario Builder 통합 서비스",
    version="0.3.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gateways (lazy 초기화)
_llm_gateway: Optional[LLMGateway] = None
_storage_gateway: Optional[StorageGateway] = None


def get_llm() -> LLMGateway:
    """LLM Gateway 싱글톤"""
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = get_llm_gateway()
    return _llm_gateway


def get_storage() -> StorageGateway:
    """Storage Gateway 싱글톤"""
    global _storage_gateway
    if _storage_gateway is None:
        _storage_gateway = get_storage_gateway()
    return _storage_gateway


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model_id: str
    provider: str
    prompt_version: str
    latency_ms: float
    timestamp: str


class ParseRequest(BaseModel):
    """Orchestrator - 자연어 파싱 요청"""
    user_request: str = Field(..., description="사용자 자연어 요구사항")
    experiment_id: Optional[str] = Field(None, description="실험 ID")


class ParseResponse(BaseModel):
    """Orchestrator - 파싱 결과"""
    success: bool
    experiment_id: str
    parsed_intent: Dict[str, Any]
    next_steps: List[str]
    timestamp: str


class ScenarioBuildRequest(BaseModel):
    """Scenario Builder - 시나리오 생성 요청"""
    user_request: str = Field(..., description="사용자 요구사항")
    experiment_id: str = Field(..., description="실험 ID")
    location: Optional[str] = Field(None, description="위치")
    duration_hours: Optional[int] = Field(None, description="시뮬레이션 시간")


class ScenarioBuildResponse(BaseModel):
    """Scenario Builder - 시나리오 생성 결과"""
    success: bool
    experiment_id: str
    scenario_id: str
    scenario_spec: Dict[str, Any]
    scenario_uri: str
    timestamp: str


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness probe"""
    return {
        "status": "healthy",
        "service": "agent-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.3.0"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes readiness probe"""
    try:
        llm = get_llm()
        storage = get_storage()

        return {
            "status": "ready",
            "service": "agent-service",
            "dependencies": {
                "llm_gateway": llm.provider_name,
                "storage_gateway": storage.provider_name,
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "agent-service",
            "error": str(e),
        }


@app.get("/")
async def root():
    """Root endpoint"""
    try:
        llm = get_llm()
        storage = get_storage()

        llm_info = {
            "provider": llm.provider_name,
            "model": llm.model_id,
        }
        storage_info = {
            "provider": storage.provider_name,
        }
    except Exception as e:
        llm_info = {"error": str(e)}
        storage_info = {"error": str(e)}

    return {
        "service": "agent-service",
        "description": "AI Agent + Orchestrator + Scenario Builder 통합 서비스",
        "version": "0.3.0",
        "modules": {
            "orchestrator": "전체 흐름 제어 및 Agent 호출",
            "scenario_builder": "자연어 → 실험 명세 변환",
            "agent": "LLM 기반 대화 및 생성"
        },
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "orchestrator_parse": "/orchestrator/parse",
            "scenario_build": "/scenario/build",
            "agent_chat": "/agent/chat",
            "agent_generate": "/agent/generate",
            "docs": "/docs"
        },
        "environment": os.getenv("ENV", "dev"),
        "gateways": {
            "llm": llm_info,
            "storage": storage_info,
        }
    }


# ============================================================================
# Orchestrator Endpoints
# ============================================================================

@app.post("/orchestrator/parse", response_model=ParseResponse)
async def parse_user_request(request: ParseRequest):
    """
    사용자 요청 파싱 및 의도 분석

    자연어 요구사항을 분석하여 실험 의도를 파악하고 다음 단계를 제시한다.
    """
    try:
        llm = get_llm()

        system_prompt = """당신은 교통 시뮬레이션 요구사항 분석 전문가입니다.
사용자의 자연어 요구사항을 분석하여 다음 정보를 추출하세요:

1. location: 위치 (지명, 도로명 등)
2. scenario_type: 시나리오 타입 (demand_change, network_change, signal_optimization 등)
3. objectives: 분석 목표 (통행시간, 대기시간, 혼잡도 등)
4. constraints: 제약조건
5. parameters: 주요 파라미터 (차량 수, 시뮬레이션 시간 등)

JSON 포맷으로 응답하세요."""

        prompt = f"다음 요구사항을 분석하세요:\n\n{request.user_request}"

        response = await llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1000,
            prompt_version="orchestrator-parse-v1.0"
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        # 간단한 JSON 파싱 (실제로는 더 robust하게)
        import json
        try:
            parsed_intent = json.loads(response.content)
        except:
            # JSON 파싱 실패 시 기본 구조
            parsed_intent = {
                "location": "unknown",
                "scenario_type": "general",
                "raw_analysis": response.content
            }

        experiment_id = request.experiment_id or f"exp-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        return ParseResponse(
            success=True,
            experiment_id=experiment_id,
            parsed_intent=parsed_intent,
            next_steps=["scenario_build", "network_build", "demand_build"],
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Scenario Builder Endpoints
# ============================================================================

@app.post("/scenario/build", response_model=ScenarioBuildResponse)
async def build_scenario(request: ScenarioBuildRequest):
    """
    시나리오 생성

    파싱된 요구사항을 바탕으로 구조화된 시나리오 명세를 생성한다.
    """
    try:
        llm = get_llm()
        storage = get_storage()

        system_prompt = """당신은 교통 시뮬레이션 시나리오 설계 전문가입니다.
사용자 요구사항을 다음 포맷의 시나리오 명세로 변환하세요:

{
  "experiment_id": "실험 ID",
  "scenario_type": "타입",
  "location": {
    "name": "위치명",
    "bbox": [경도최소, 위도최소, 경도최대, 위도최대],
    "center": [경도, 위도]
  },
  "simulation_config": {
    "duration_hours": 1,
    "time_step": 1,
    "start_time": "00:00:00"
  },
  "baseline": {
    "vehicle_count": 1000,
    "vehicle_types": ["car", "bus", "truck"]
  },
  "variants": [
    {
      "variant_id": "baseline",
      "description": "기준선",
      "parameters": {}
    },
    {
      "variant_id": "scenario-1",
      "description": "변형 시나리오",
      "parameters": {
        "demand_multiplier": 1.2
      }
    }
  ],
  "kpis": ["avg_travel_time", "avg_waiting_time", "throughput"],
  "objectives": ["목표1", "목표2"]
}

완전한 JSON만 응답하세요."""

        prompt = f"""요구사항: {request.user_request}
위치: {request.location or '자동 추출'}
시뮬레이션 시간: {request.duration_hours or 1}시간

위 정보로 시나리오 명세를 생성하세요."""

        response = await llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000,
            prompt_version="scenario-build-v2.0"
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        # JSON 파싱
        import json
        try:
            scenario_spec = json.loads(response.content)
        except:
            # 기본 시나리오 구조
            scenario_spec = {
                "experiment_id": request.experiment_id,
                "scenario_type": "general",
                "location": {"name": request.location or "unknown"},
                "raw_spec": response.content
            }

        # 시나리오 ID
        scenario_id = f"scenario-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # S3에 저장
        scenario_content = json.dumps(scenario_spec, indent=2, ensure_ascii=False).encode()
        scenario_uri = await storage.upload(
            f"scenarios/{request.experiment_id}/{scenario_id}.json",
            scenario_content,
            content_type="application/json",
            metadata={
                "experiment_id": request.experiment_id,
                "created_at": datetime.utcnow().isoformat(),
                "model_id": response.model_id,
            }
        )

        return ScenarioBuildResponse(
            success=True,
            experiment_id=request.experiment_id,
            scenario_id=scenario_id,
            scenario_spec=scenario_spec,
            scenario_uri=scenario_uri,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Agent Endpoints (기존 유지)
# ============================================================================

@app.post("/agent/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    채팅 엔드포인트 (LLM Gateway 통합)

    LLM Gateway를 통해 실제 LLM을 호출한다.
    """
    try:
        llm = get_llm()

        system_prompt = """당신은 교통 시뮬레이션 전문 AI 어시스턴트입니다.
사용자의 교통 시뮬레이션 요구사항을 이해하고 명확한 실험 계획을 제시합니다."""

        response = await llm.generate(
            prompt=request.message,
            system_prompt=system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            prompt_version="chat-v1.0",
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        return ChatResponse(
            response=response.content,
            conversation_id=request.conversation_id or "new-conversation",
            model_id=response.model_id,
            provider=response.provider,
            prompt_version=response.prompt_version,
            latency_ms=response.latency_ms,
            timestamp=response.timestamp.isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/generate")
async def generate_text(request: dict):
    """
    텍스트 생성 엔드포인트 (범용)

    프롬프트를 받아 LLM으로 텍스트를 생성한다.
    """
    try:
        llm = get_llm()

        prompt = request.get("prompt", "")
        system_prompt = request.get("system_prompt", None)
        temperature = request.get("temperature", 0.7)
        max_tokens = request.get("max_tokens", 1000)

        response = await llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_version="generate-v1.0",
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        return {
            "success": True,
            "content": response.content,
            "metadata": {
                "model_id": response.model_id,
                "provider": response.provider,
                "latency_ms": response.latency_ms,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
