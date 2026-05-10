"""
Simulation Schema

SUMO 시뮬레이션 실행 요청 및 산출물 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class SimulationRunRequest(BaseModel):
    """
    시뮬레이션 실행 요청

    SUMO 시뮬레이션 실행 요청
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    request_id: str = Field(
        ...,
        description="요청 ID",
        examples=["simreq-20260507-001"]
    )

    experiment_id: str = Field(
        ...,
        description="실험 ID",
        examples=["exp-20260507-001"]
    )

    variant_id: str = Field(
        ...,
        description="시나리오 변형 ID",
        examples=["base-001"]
    )

    network_artifact_id: str = Field(
        ...,
        description="도로망 산출물 ID",
        examples=["net-20260507-001"]
    )

    demand_artifact_id: str = Field(
        ...,
        description="수요 산출물 ID",
        examples=["dem-20260507-001"]
    )

    simulation_settings: dict = Field(
        ...,
        description="시뮬레이션 실행 설정",
        examples=[{
            "step_length": 1.0,
            "begin": 0,
            "end": 7200,
            "output_types": ["tripinfo", "summary", "emissions"],
            "random_seed": 42
        }]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="요청 생성 시각"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "request_id": "simreq-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "variant_id": "base-001",
                    "network_artifact_id": "net-20260507-001",
                    "demand_artifact_id": "dem-20260507-001",
                    "simulation_settings": {
                        "step_length": 1.0,
                        "begin": 0,
                        "end": 7200,
                        "output_types": ["tripinfo", "summary", "emissions", "queue"],
                        "random_seed": 42,
                        "gui": False,
                        "collision_action": "warn"
                    },
                    "created_at": "2026-05-07T12:20:00Z"
                }
            ]
        }


class SimulationRunArtifact(BaseModel):
    """
    시뮬레이션 산출물

    SUMO 실행 후 생성된 결과 파일들
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    artifact_id: str = Field(
        ...,
        description="산출물 ID",
        examples=["sim-20260507-001"]
    )

    request_id: str = Field(
        ...,
        description="요청 ID",
        examples=["simreq-20260507-001"]
    )

    experiment_id: str = Field(
        ...,
        description="실험 ID",
        examples=["exp-20260507-001"]
    )

    variant_id: str = Field(
        ...,
        description="시나리오 변형 ID",
        examples=["base-001"]
    )

    uri: str = Field(
        ...,
        description="시뮬레이션 결과 디렉토리 URI",
        examples=["s3://agent-t-simulations/exp-20260507-001/base-001/"]
    )

    output_files: dict = Field(
        ...,
        description="출력 파일 목록",
        examples=[{
            "tripinfo": "s3://agent-t-simulations/exp-20260507-001/base-001/tripinfo.xml",
            "summary": "s3://agent-t-simulations/exp-20260507-001/base-001/summary.xml",
            "emissions": "s3://agent-t-simulations/exp-20260507-001/base-001/emissions.xml"
        }]
    )

    status: Literal["completed", "failed", "timeout"] = Field(
        ...,
        description="실행 상태"
    )

    statistics: dict = Field(
        ...,
        description="시뮬레이션 통계",
        examples=[{
            "simulated_time_seconds": 7200,
            "total_vehicles": 5000,
            "completed_trips": 4987,
            "teleports": 13,
            "collisions": 0,
            "runtime_seconds": 125.4
        }]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )

    generated_by: Optional[str] = Field(
        default=None,
        description="생성 도구",
        examples=["sumo-1.18.0"]
    )

    error_message: Optional[str] = Field(
        default=None,
        description="오류 메시지 (실패 시)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "artifact_id": "sim-20260507-001",
                    "request_id": "simreq-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "variant_id": "base-001",
                    "uri": "s3://agent-t-simulations/exp-20260507-001/base-001/",
                    "output_files": {
                        "tripinfo": "s3://agent-t-simulations/exp-20260507-001/base-001/tripinfo.xml",
                        "summary": "s3://agent-t-simulations/exp-20260507-001/base-001/summary.xml",
                        "emissions": "s3://agent-t-simulations/exp-20260507-001/base-001/emissions.xml",
                        "queue": "s3://agent-t-simulations/exp-20260507-001/base-001/queue.xml"
                    },
                    "status": "completed",
                    "statistics": {
                        "simulated_time_seconds": 7200,
                        "total_vehicles": 5000,
                        "completed_trips": 4987,
                        "teleports": 13,
                        "collisions": 0,
                        "avg_trip_duration_seconds": 1245.6,
                        "avg_waiting_time_seconds": 89.3,
                        "runtime_seconds": 125.4
                    },
                    "created_at": "2026-05-07T12:25:00Z",
                    "generated_by": "sumo-1.18.0",
                    "error_message": None
                }
            ]
        }
