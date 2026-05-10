"""
Scenario Builder Output Models

ScenarioBuilder의 출력 모델
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ScenarioBuilderOutput(BaseModel):
    """
    Scenario Builder 출력

    ScenarioPlan + NetworkBuildRequest + DemandBuildRequest 목록
    """

    scenario_plan: dict = Field(
        ...,
        description="생성된 시나리오 계획 (ScenarioPlan JSON)"
    )

    network_requests: list[dict] = Field(
        ...,
        description="도로망 생성 요청 목록 (NetworkBuildRequest JSON)",
        min_length=1
    )

    demand_requests: list[dict] = Field(
        ...,
        description="수요 생성 요청 목록 (DemandBuildRequest JSON)",
        min_length=1
    )

    experiment_id: str = Field(
        ...,
        description="실험 ID"
    )

    baseline_variant_id: str = Field(
        ...,
        description="Baseline 변형 ID"
    )

    alternative_variant_ids: list[str] = Field(
        ...,
        description="Alternative 변형 ID 목록",
        min_length=1
    )

    processing_time_ms: float = Field(
        ...,
        description="처리 시간 (ms)"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )


class ScenarioModification(BaseModel):
    """
    시나리오 수정 사항

    Alternative 시나리오에 적용할 변경 사항
    """

    modification_type: str = Field(
        ...,
        description="수정 타입",
        examples=["traffic_light", "lane_change", "demand_multiplier"]
    )

    target: str = Field(
        ...,
        description="수정 대상",
        examples=["junction-001", "edge-045", "all"]
    )

    parameters: dict = Field(
        ...,
        description="수정 파라미터"
    )

    description: str = Field(
        ...,
        description="수정 설명"
    )
