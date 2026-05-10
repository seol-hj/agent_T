"""
Analysis Schema

시뮬레이션 결과 분석 및 KPI 비교 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BaselineKPI(BaseModel):
    """
    Baseline 시나리오 KPI

    현재 상태의 성능 지표
    """

    variant_id: str = Field(
        ...,
        description="Baseline 변형 ID",
        examples=["base-001"]
    )

    avg_trip_duration_seconds: float = Field(
        ...,
        description="평균 통행 시간 (초)",
        examples=[1245.6]
    )

    avg_waiting_time_seconds: float = Field(
        ...,
        description="평균 대기 시간 (초)",
        examples=[89.3]
    )

    total_co2_kg: float = Field(
        ...,
        description="총 CO2 배출량 (kg)",
        examples=[2456.8]
    )

    avg_speed_kmh: float = Field(
        ...,
        description="평균 속도 (km/h)",
        examples=[28.5]
    )

    completed_trips: int = Field(
        ...,
        description="완료된 통행 수",
        examples=[4987]
    )

    teleports: int = Field(
        ...,
        description="텔레포트 발생 횟수",
        examples=[13]
    )


class AlternativeKPI(BaseModel):
    """
    Alternative 시나리오 KPI

    비교 대상 시나리오의 성능 지표 및 개선율
    """

    variant_id: str = Field(
        ...,
        description="Alternative 변형 ID",
        examples=["alt-signal-001"]
    )

    avg_trip_duration_seconds: float = Field(
        ...,
        description="평균 통행 시간 (초)",
        examples=[1045.2]
    )

    avg_waiting_time_seconds: float = Field(
        ...,
        description="평균 대기 시간 (초)",
        examples=[62.7]
    )

    total_co2_kg: float = Field(
        ...,
        description="총 CO2 배출량 (kg)",
        examples=[2089.4]
    )

    avg_speed_kmh: float = Field(
        ...,
        description="평균 속도 (km/h)",
        examples=[34.2]
    )

    completed_trips: int = Field(
        ...,
        description="완료된 통행 수",
        examples=[4995]
    )

    teleports: int = Field(
        ...,
        description="텔레포트 발생 횟수",
        examples=[5]
    )

    improvements: dict = Field(
        ...,
        description="Baseline 대비 개선율 (%)",
        examples=[{
            "trip_duration": -16.1,
            "waiting_time": -29.8,
            "co2_emission": -15.0,
            "speed": 20.0
        }]
    )


class KPIComparison(BaseModel):
    """
    KPI 비교

    Baseline과 Alternative 시나리오 간 성능 비교
    """

    baseline: BaselineKPI = Field(
        ...,
        description="Baseline 시나리오 KPI"
    )

    alternatives: list[AlternativeKPI] = Field(
        ...,
        description="Alternative 시나리오 KPI 목록",
        min_length=1
    )

    best_alternative_id: str = Field(
        ...,
        description="최적 Alternative 변형 ID",
        examples=["alt-signal-001"]
    )

    recommendation_summary: str = Field(
        ...,
        description="권장사항 요약",
        examples=["신호 체계 최적화로 통행 시간 16.1% 단축, 배출량 15.0% 감소 예상"]
    )


class AnalysisResult(BaseModel):
    """
    분석 결과

    시뮬레이션 산출물 분석 결과 및 KPI 비교
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    analysis_id: str = Field(
        ...,
        description="분석 ID",
        examples=["ana-20260507-001"]
    )

    experiment_id: str = Field(
        ...,
        description="실험 ID",
        examples=["exp-20260507-001"]
    )

    simulation_artifact_ids: list[str] = Field(
        ...,
        description="분석 대상 시뮬레이션 산출물 ID 목록",
        examples=[["sim-20260507-001", "sim-20260507-002"]]
    )

    kpi_comparison: KPIComparison = Field(
        ...,
        description="KPI 비교 결과"
    )

    detailed_metrics: dict = Field(
        default_factory=dict,
        description="상세 지표",
        examples=[{
            "congestion_hotspots": ["junction-001", "edge-045"],
            "peak_queue_length": 45,
            "bottleneck_analysis": "교차로 junction-001에서 신호 타이밍 비효율"
        }]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )

    generated_by: Optional[dict] = Field(
        default=None,
        description="생성 정보",
        examples=[{
            "analyzer_version": "analyzer-v1.0",
            "python_version": "3.11.0"
        }]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "analysis_id": "ana-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "simulation_artifact_ids": ["sim-20260507-001", "sim-20260507-002"],
                    "kpi_comparison": {
                        "baseline": {
                            "variant_id": "base-001",
                            "avg_trip_duration_seconds": 1245.6,
                            "avg_waiting_time_seconds": 89.3,
                            "total_co2_kg": 2456.8,
                            "avg_speed_kmh": 28.5,
                            "completed_trips": 4987,
                            "teleports": 13
                        },
                        "alternatives": [
                            {
                                "variant_id": "alt-signal-001",
                                "avg_trip_duration_seconds": 1045.2,
                                "avg_waiting_time_seconds": 62.7,
                                "total_co2_kg": 2089.4,
                                "avg_speed_kmh": 34.2,
                                "completed_trips": 4995,
                                "teleports": 5,
                                "improvements": {
                                    "trip_duration": -16.1,
                                    "waiting_time": -29.8,
                                    "co2_emission": -15.0,
                                    "speed": 20.0,
                                    "completed_trips": 0.16,
                                    "teleports": -61.5
                                }
                            }
                        ],
                        "best_alternative_id": "alt-signal-001",
                        "recommendation_summary": "신호 체계 최적화로 통행 시간 16.1% 단축, 배출량 15.0% 감소 예상"
                    },
                    "detailed_metrics": {
                        "congestion_hotspots": [
                            {"junction_id": "junction-001", "avg_queue_length": 12.5},
                            {"edge_id": "edge-045", "avg_occupancy": 0.85}
                        ],
                        "peak_queue_length": 45,
                        "bottleneck_analysis": "교차로 junction-001에서 신호 타이밍 비효율",
                        "emission_breakdown": {
                            "passenger": 1876.3,
                            "bus": 156.2,
                            "truck": 56.9
                        }
                    },
                    "created_at": "2026-05-07T12:30:00Z",
                    "generated_by": {
                        "analyzer_version": "analyzer-v1.0",
                        "python_version": "3.11.0"
                    }
                }
            ]
        }
