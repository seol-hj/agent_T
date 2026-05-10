"""
Logging Schema

에이전트 로그 및 추적 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    """로그 레벨"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AgentLog(BaseModel):
    """
    에이전트 로그

    Agent 실행 중 발생하는 이벤트 로그
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    log_id: str = Field(
        ...,
        description="로그 ID",
        examples=["log-20260507-123456-001"]
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="로그 발생 시각"
    )

    level: LogLevel = Field(
        ...,
        description="로그 레벨"
    )

    agent_name: str = Field(
        ...,
        description="에이전트 이름",
        examples=["scenario-builder", "network-builder", "analyzer"]
    )

    experiment_id: Optional[str] = Field(
        default=None,
        description="실험 ID (있는 경우)",
        examples=["exp-20260507-001"]
    )

    request_id: Optional[str] = Field(
        default=None,
        description="요청 ID (있는 경우)",
        examples=["req-20260507-123456"]
    )

    message: str = Field(
        ...,
        description="로그 메시지",
        examples=["시나리오 생성 시작", "도로망 변환 완료", "시뮬레이션 실행 실패"]
    )

    context: Optional[dict] = Field(
        default=None,
        description="추가 컨텍스트 정보",
        examples=[{
            "variant_id": "base-001",
            "step": "network_build",
            "duration_ms": 1250.5
        }]
    )

    error_details: Optional[dict] = Field(
        default=None,
        description="오류 상세 정보 (오류 발생 시)",
        examples=[{
            "error_type": "ValidationError",
            "error_message": "Invalid OSM bounding box",
            "stack_trace": "..."
        }]
    )

    llm_metadata: Optional[dict] = Field(
        default=None,
        description="LLM 호출 메타데이터 (LLM 사용 시)",
        examples=[{
            "model_id": "anthropic.claude-3-sonnet",
            "prompt_version": "scenario-gen-v2.0",
            "input_tokens": 1200,
            "output_tokens": 450,
            "latency_ms": 1250.5
        }]
    )

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "log_id": "log-20260507-123456-001",
                    "timestamp": "2026-05-07T12:00:00.123Z",
                    "level": "info",
                    "agent_name": "scenario-builder",
                    "experiment_id": "exp-20260507-001",
                    "request_id": "req-20260507-123456",
                    "message": "시나리오 생성 완료",
                    "context": {
                        "variant_count": 2,
                        "baseline_id": "base-001",
                        "alternative_ids": ["alt-signal-001"],
                        "duration_ms": 1250.5
                    },
                    "error_details": None,
                    "llm_metadata": {
                        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                        "prompt_version": "scenario-gen-v2.0",
                        "input_tokens": 1200,
                        "output_tokens": 450,
                        "latency_ms": 1250.5,
                        "provider": "bedrock"
                    }
                },
                {
                    "schema_version": "1.0",
                    "log_id": "log-20260507-123456-002",
                    "timestamp": "2026-05-07T12:05:30.456Z",
                    "level": "error",
                    "agent_name": "network-builder",
                    "experiment_id": "exp-20260507-001",
                    "request_id": "netreq-20260507-001",
                    "message": "OSM 데이터 다운로드 실패",
                    "context": {
                        "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
                        "retry_count": 3,
                        "duration_ms": 15000.0
                    },
                    "error_details": {
                        "error_type": "ConnectionError",
                        "error_message": "Connection timeout to Overpass API",
                        "stack_trace": "Traceback (most recent call last):\n  File ...",
                        "retry_after_seconds": 60
                    },
                    "llm_metadata": None
                }
            ]
        }
