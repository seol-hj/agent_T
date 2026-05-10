"""
Versioning Schema

모델 및 프롬프트 버전 관리 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ModelVersion(BaseModel):
    """
    모델 버전

    LLM 모델 버전 정보 및 메타데이터
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    model_id: str = Field(
        ...,
        description="모델 ID",
        examples=["anthropic.claude-3-sonnet-20240229-v1:0"]
    )

    model_name: str = Field(
        ...,
        description="모델 이름",
        examples=["Claude 3 Sonnet"]
    )

    provider: str = Field(
        ...,
        description="모델 제공자",
        examples=["bedrock", "openai", "local"]
    )

    version: str = Field(
        ...,
        description="버전 번호",
        examples=["20240229-v1:0"]
    )

    capabilities: list[str] = Field(
        ...,
        description="모델 능력",
        examples=[["text-generation", "structured-output", "function-calling"]]
    )

    context_window: int = Field(
        ...,
        description="컨텍스트 윈도우 (토큰 수)",
        examples=[200000]
    )

    max_output_tokens: int = Field(
        ...,
        description="최대 출력 토큰 수",
        examples=[4096]
    )

    supports_streaming: bool = Field(
        default=False,
        description="스트리밍 지원 여부"
    )

    cost_per_1k_input_tokens: Optional[float] = Field(
        default=None,
        description="1K 입력 토큰당 비용 (USD)",
        examples=[0.003]
    )

    cost_per_1k_output_tokens: Optional[float] = Field(
        default=None,
        description="1K 출력 토큰당 비용 (USD)",
        examples=[0.015]
    )

    deprecated: bool = Field(
        default=False,
        description="폐기 여부"
    )

    deprecated_at: Optional[datetime] = Field(
        default=None,
        description="폐기 시각"
    )

    replacement_model_id: Optional[str] = Field(
        default=None,
        description="대체 모델 ID",
        examples=["anthropic.claude-3-sonnet-20250315-v1:0"]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="등록 시각"
    )

    notes: Optional[str] = Field(
        default=None,
        description="비고",
        examples=["프로덕션 환경에서 사용 권장"]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "model_name": "Claude 3 Sonnet",
                    "provider": "bedrock",
                    "version": "20240229-v1:0",
                    "capabilities": [
                        "text-generation",
                        "structured-output",
                        "function-calling",
                        "multilingual"
                    ],
                    "context_window": 200000,
                    "max_output_tokens": 4096,
                    "supports_streaming": True,
                    "cost_per_1k_input_tokens": 0.003,
                    "cost_per_1k_output_tokens": 0.015,
                    "deprecated": False,
                    "deprecated_at": None,
                    "replacement_model_id": None,
                    "created_at": "2026-05-07T12:00:00Z",
                    "notes": "프로덕션 환경에서 사용 권장. 한국어 처리 성능 우수."
                }
            ]
        }


class PromptVersion(BaseModel):
    """
    프롬프트 버전

    LLM 프롬프트 템플릿 버전 관리
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    prompt_id: str = Field(
        ...,
        description="프롬프트 ID",
        examples=["scenario-gen-v2.0"]
    )

    prompt_name: str = Field(
        ...,
        description="프롬프트 이름",
        examples=["시나리오 생성 프롬프트"]
    )

    version: str = Field(
        ...,
        description="버전 번호",
        examples=["v2.0"]
    )

    agent_name: str = Field(
        ...,
        description="사용하는 에이전트 이름",
        examples=["scenario-builder"]
    )

    template: str = Field(
        ...,
        description="프롬프트 템플릿 내용",
        examples=["당신은 교통 시뮬레이션 시나리오를 생성하는 AI 전문가입니다..."]
    )

    template_variables: list[str] = Field(
        ...,
        description="템플릿 변수 목록",
        examples=[["user_input", "location", "time_period"]]
    )

    expected_output_format: str = Field(
        ...,
        description="기대 출력 형식",
        examples=["json", "yaml", "markdown"]
    )

    output_schema_ref: Optional[str] = Field(
        default=None,
        description="출력 스키마 참조",
        examples=["ExperimentSpec"]
    )

    compatible_models: list[str] = Field(
        ...,
        description="호환 가능한 모델 ID 목록",
        examples=[["anthropic.claude-3-sonnet-20240229-v1:0", "anthropic.claude-3-opus-20240229-v1:0"]]
    )

    active: bool = Field(
        default=True,
        description="활성화 여부"
    )

    performance_metrics: Optional[dict] = Field(
        default=None,
        description="성능 지표",
        examples=[{
            "avg_latency_ms": 1250.5,
            "avg_input_tokens": 1200,
            "avg_output_tokens": 450,
            "success_rate": 0.98
        }]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        description="마지막 수정 시각"
    )

    changelog: Optional[list[str]] = Field(
        default=None,
        description="변경 이력",
        examples=[["v2.0: 한국어 자연어 처리 개선", "v1.5: 출력 JSON 스키마 명확화"]]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "prompt_id": "scenario-gen-v2.0",
                    "prompt_name": "시나리오 생성 프롬프트",
                    "version": "v2.0",
                    "agent_name": "scenario-builder",
                    "template": "당신은 교통 시뮬레이션 시나리오를 생성하는 AI 전문가입니다.\n\n사용자 입력: {user_input}\n위치: {location}\n시간대: {time_period}\n\n위 정보를 바탕으로 ExperimentSpec JSON을 생성하세요.",
                    "template_variables": [
                        "user_input",
                        "location",
                        "time_period"
                    ],
                    "expected_output_format": "json",
                    "output_schema_ref": "ExperimentSpec",
                    "compatible_models": [
                        "anthropic.claude-3-sonnet-20240229-v1:0",
                        "anthropic.claude-3-opus-20240229-v1:0"
                    ],
                    "active": True,
                    "performance_metrics": {
                        "avg_latency_ms": 1250.5,
                        "avg_input_tokens": 1200,
                        "avg_output_tokens": 450,
                        "success_rate": 0.98,
                        "total_invocations": 234
                    },
                    "created_at": "2026-05-01T10:00:00Z",
                    "updated_at": "2026-05-07T12:00:00Z",
                    "changelog": [
                        "v2.0: 한국어 자연어 처리 개선, 예시 추가",
                        "v1.5: 출력 JSON 스키마 명확화",
                        "v1.0: 초기 버전"
                    ]
                }
            ]
        }
