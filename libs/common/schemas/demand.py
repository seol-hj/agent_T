"""
Demand Schema

교통 수요 생성 요청 및 산출물 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class DemandBuildRequest(BaseModel):
    """
    교통 수요 생성 요청

    통행 패턴 및 차량 경로 생성 요청
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    request_id: str = Field(
        ...,
        description="요청 ID",
        examples=["demreq-20260507-001"]
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

    demand_settings: dict = Field(
        ...,
        description="수요 생성 설정",
        examples=[{
            "vehicle_count": 5000,
            "start_time": 0,
            "end_time": 7200,
            "vehicle_types": {
                "passenger": 0.8,
                "bus": 0.1,
                "truck": 0.1
            },
            "trip_distribution": "random",
            "origin_zones": ["zone-1", "zone-2"],
            "destination_zones": ["zone-3", "zone-4"]
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
                    "request_id": "demreq-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "variant_id": "base-001",
                    "network_artifact_id": "net-20260507-001",
                    "demand_settings": {
                        "vehicle_count": 5000,
                        "start_time": 0,
                        "end_time": 7200,
                        "vehicle_types": {
                            "passenger": 0.8,
                            "bus": 0.1,
                            "truck": 0.1
                        },
                        "trip_distribution": "random",
                        "origin_zones": ["residential_north", "residential_east"],
                        "destination_zones": ["business_center", "industrial_south"],
                        "departure_distribution": "rush_hour"
                    },
                    "created_at": "2026-05-07T12:10:00Z"
                }
            ]
        }


class DemandArtifact(BaseModel):
    """
    교통 수요 산출물

    생성된 차량 경로 파일
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    artifact_id: str = Field(
        ...,
        description="산출물 ID",
        examples=["dem-20260507-001"]
    )

    request_id: str = Field(
        ...,
        description="요청 ID",
        examples=["demreq-20260507-001"]
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
        description="경로 파일 URI",
        examples=["s3://agent-t-demand/exp-20260507-001/base-001/routes.rou.xml"]
    )

    file_format: Literal["rou.xml"] = Field(
        default="rou.xml",
        description="파일 포맷"
    )

    file_size_bytes: int = Field(
        ...,
        description="파일 크기 (bytes)",
        examples=[2048000]
    )

    statistics: dict = Field(
        ...,
        description="수요 통계",
        examples=[{
            "total_vehicles": 5000,
            "vehicles_by_type": {
                "passenger": 4000,
                "bus": 500,
                "truck": 500
            },
            "total_trips": 5000,
            "avg_trip_length_km": 8.5,
            "departure_time_range": [0, 7200]
        }]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )

    generated_by: Optional[str] = Field(
        default=None,
        description="생성 도구",
        examples=["duarouter-1.18.0"]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "artifact_id": "dem-20260507-001",
                    "request_id": "demreq-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "variant_id": "base-001",
                    "uri": "s3://agent-t-demand/exp-20260507-001/base-001/routes.rou.xml",
                    "file_format": "rou.xml",
                    "file_size_bytes": 2048000,
                    "statistics": {
                        "total_vehicles": 5000,
                        "vehicles_by_type": {
                            "passenger": 4000,
                            "bus": 500,
                            "truck": 500
                        },
                        "total_trips": 5000,
                        "avg_trip_length_km": 8.5,
                        "departure_time_range": [0, 7200]
                    },
                    "created_at": "2026-05-07T12:15:00Z",
                    "generated_by": "duarouter-1.18.0"
                }
            ]
        }
