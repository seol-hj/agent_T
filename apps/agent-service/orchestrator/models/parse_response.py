"""
Parse Response Models

Orchestrator의 응답 모델
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ParseResponse(BaseModel):
    """
    자연어 파싱 응답

    ExperimentSpec 생성 결과 또는 보완 질문
    """

    status: Literal["success", "needs_clarification", "error"] = Field(
        ...,
        description="파싱 상태"
    )

    experiment_spec: Optional[dict] = Field(
        default=None,
        description="생성된 실험 명세 (ExperimentSpec JSON)"
    )

    missing_fields: Optional[list[str]] = Field(
        default=None,
        description="누락된 필수 필드 목록",
        examples=[["location.bbox", "time_settings.start_time"]]
    )

    clarification_question: Optional[str] = Field(
        default=None,
        description="사용자에게 묻는 보완 질문",
        examples=["시뮬레이션할 지역의 위치를 알려주세요. 예: 서울 강남구"]
    )

    request_type: Optional[str] = Field(
        default=None,
        description="탐지된 요청 타입",
        examples=["demand_increase", "lane_change", "signal_timing_change"]
    )

    confidence_score: Optional[float] = Field(
        default=None,
        description="파싱 신뢰도 (0.0-1.0)",
        examples=[0.85]
    )

    processing_time_ms: float = Field(
        ...,
        description="처리 시간 (ms)"
    )

    llm_metadata: Optional[dict] = Field(
        default=None,
        description="LLM 호출 메타데이터"
    )

    error_message: Optional[str] = Field(
        default=None,
        description="오류 메시지 (오류 시)"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="응답 생성 시각"
    )


class RAGContext(BaseModel):
    """
    RAG 컨텍스트

    사용자 요청 해석에 참고할 추가 컨텍스트
    """

    context_type: Literal["previous_experiment", "domain_knowledge", "user_preference"] = Field(
        ...,
        description="컨텍스트 타입"
    )

    content: str = Field(
        ...,
        description="컨텍스트 내용"
    )

    relevance_score: Optional[float] = Field(
        default=None,
        description="관련도 점수 (0.0-1.0)"
    )

    source: Optional[str] = Field(
        default=None,
        description="컨텍스트 출처"
    )
