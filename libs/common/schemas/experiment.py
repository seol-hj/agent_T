"""
Experiment Schema

실험 명세 및 시나리오 계획 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class ScenarioType(str, Enum):
    """시나리오 타입"""
    BASELINE = "baseline"
    ALTERNATIVE = "alternative"


class ScenarioVariant(BaseModel):
    """
    시나리오 변형

    Base 또는 Alternative 시나리오의 구체적인 설정
    """

    variant_id: str = Field(
        ...,
        description="변형 ID",
        examples=["base-001", "alt-signal-001"]
    )

    variant_type: ScenarioType = Field(
        ...,
        description="변형 타입 (baseline | alternative)"
    )

    name: str = Field(
        ...,
        description="변형 이름",
        examples=["현재 신호 체계", "최적화된 신호 체계"]
    )

    description: str = Field(
        ...,
        description="변형 설명",
        examples=["현재 강남구에 적용된 신호등 타이밍"]
    )

    parameters: dict = Field(
        ...,
        description="시나리오 파라미터",
        examples=[{
            "signal_cycle": 120,
            "green_time": 60,
            "red_time": 60
        }]
    )

    class Config:
        use_enum_values = True


class ScenarioPlan(BaseModel):
    """
    시나리오 계획

    Base 시나리오와 Alternative 시나리오(들)을 포함
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    plan_id: str = Field(
        ...,
        description="계획 ID",
        examples=["plan-20260507-001"]
    )

    experiment_id: str = Field(
        ...,
        description="실험 ID",
        examples=["exp-20260507-001"]
    )

    baseline: ScenarioVariant = Field(
        ...,
        description="Base 시나리오 (현재 상태)"
    )

    alternatives: list[ScenarioVariant] = Field(
        ...,
        description="Alternative 시나리오들 (비교 대상)",
        min_length=1
    )

    comparison_objectives: list[str] = Field(
        ...,
        description="비교 목표",
        examples=[["평균 통행 시간 단축", "배출량 감소", "교통 혼잡도 개선"]]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "plan_id": "plan-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "baseline": {
                        "variant_id": "base-001",
                        "variant_type": "baseline",
                        "name": "현재 신호 체계",
                        "description": "현재 강남구 적용 중인 신호등 타이밍",
                        "parameters": {
                            "signal_cycle": 120,
                            "green_time": 60,
                            "red_time": 60
                        }
                    },
                    "alternatives": [
                        {
                            "variant_id": "alt-signal-001",
                            "variant_type": "alternative",
                            "name": "최적화된 신호 체계",
                            "description": "AI 기반으로 최적화된 신호등 타이밍",
                            "parameters": {
                                "signal_cycle": 90,
                                "green_time": 50,
                                "red_time": 40
                            }
                        }
                    ],
                    "comparison_objectives": [
                        "평균 통행 시간 단축",
                        "배출량 감소",
                        "교통 혼잡도 개선"
                    ],
                    "created_at": "2026-05-07T12:00:00Z"
                }
            ]
        }


class ExperimentSpec(BaseModel):
    """
    실험 명세

    자연어 입력에서 추출된 구조화된 실험 명세
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    experiment_id: str = Field(
        ...,
        description="실험 고유 ID",
        examples=["exp-20260507-001"]
    )

    request_id: str = Field(
        ...,
        description="원본 요청 ID",
        examples=["req-20260507-123456"]
    )

    title: str = Field(
        ...,
        description="실험 제목",
        examples=["강남구 출퇴근 시간대 신호등 최적화 효과 분석"]
    )

    description: str = Field(
        ...,
        description="실험 설명",
        examples=["서울 강남구 출퇴근 시간대의 교통 혼잡을 완화하기 위한 신호등 최적화 방안 비교"]
    )

    location: dict = Field(
        ...,
        description="시뮬레이션 위치",
        examples=[{
            "region": "서울특별시 강남구",
            "bbox": [127.0, 37.4, 127.1, 37.5],
            "osm_query": "Gangnam-gu, Seoul, South Korea"
        }]
    )

    time_settings: dict = Field(
        ...,
        description="시간 설정",
        examples=[{
            "start_time": "07:00",
            "end_time": "09:00",
            "duration_hours": 2,
            "time_period": "weekday_morning_rush"
        }]
    )

    traffic_settings: dict = Field(
        ...,
        description="교통 설정",
        examples=[{
            "vehicle_count": 5000,
            "vehicle_types": ["passenger", "bus", "truck"],
            "demand_level": "high"
        }]
    )

    objectives: list[str] = Field(
        ...,
        description="실험 목표",
        examples=[["통행 시간 단축", "배출량 감소", "혼잡도 개선"]]
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="제약 조건",
        examples=[["예산 제약", "기존 인프라 유지"]]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )

    generated_by: Optional[dict] = Field(
        default=None,
        description="생성 정보 (LLM 메타데이터)",
        examples=[{
            "model_id": "anthropic.claude-3-sonnet",
            "provider": "bedrock",
            "prompt_version": "scenario-gen-v2.0"
        }]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "experiment_id": "exp-20260507-001",
                    "request_id": "req-20260507-123456",
                    "title": "강남구 출퇴근 시간대 신호등 최적화 효과 분석",
                    "description": "서울 강남구 출퇴근 시간대의 교통 혼잡을 완화하기 위한 신호등 최적화 방안 비교",
                    "location": {
                        "region": "서울특별시 강남구",
                        "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
                        "osm_query": "Gangnam-gu, Seoul, South Korea"
                    },
                    "time_settings": {
                        "start_time": "07:00",
                        "end_time": "09:00",
                        "duration_hours": 2,
                        "time_period": "weekday_morning_rush"
                    },
                    "traffic_settings": {
                        "vehicle_count": 5000,
                        "vehicle_types": ["passenger", "bus", "truck"],
                        "vehicle_distribution": {
                            "passenger": 0.8,
                            "bus": 0.1,
                            "truck": 0.1
                        },
                        "demand_level": "high"
                    },
                    "objectives": [
                        "평균 통행 시간 20% 단축",
                        "차량 배출량 15% 감소",
                        "교통 혼잡도 30% 개선"
                    ],
                    "constraints": [
                        "기존 도로 인프라 유지",
                        "예산 제약 내 실현 가능한 방안"
                    ],
                    "created_at": "2026-05-07T12:00:00Z",
                    "generated_by": {
                        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                        "provider": "bedrock",
                        "prompt_version": "scenario-gen-v2.0",
                        "latency_ms": 1250.5
                    }
                }
            ]
        }
