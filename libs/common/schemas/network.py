"""
Network Schema

도로망 생성 요청 및 산출물 스키마
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime


class NetworkBuildRequest(BaseModel):
    """
    도로망 생성 요청

    OSM 데이터로부터 SUMO 도로망 생성 요청
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    request_id: str = Field(
        ...,
        description="요청 ID",
        examples=["netreq-20260507-001"]
    )

    experiment_id: str = Field(
        ...,
        description="실험 ID",
        examples=["exp-20260507-001"]
    )

    variant_id: str = Field(
        ...,
        description="시나리오 변형 ID",
        examples=["base-001", "alt-signal-001"]
    )

    osm_source: dict = Field(
        ...,
        description="OSM 데이터 소스",
        examples=[{
            "type": "bbox",
            "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
            "query": "Gangnam-gu, Seoul, South Korea"
        }]
    )

    network_options: dict = Field(
        default_factory=dict,
        description="도로망 생성 옵션",
        examples=[{
            "vehicle_types": ["passenger", "bus", "truck"],
            "remove_edges": [],
            "keep_edges": [],
            "speed_limits": True
        }]
    )

    modifications: Optional[list[dict]] = Field(
        default=None,
        description="도로망 수정 사항 (Alternative 시나리오용)",
        examples=[[
            {
                "type": "traffic_light",
                "junction_id": "junction-001",
                "cycle": 90,
                "phases": [
                    {"duration": 50, "state": "GGrr"},
                    {"duration": 40, "state": "rrGG"}
                ]
            }
        ]]
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
                    "request_id": "netreq-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "variant_id": "base-001",
                    "osm_source": {
                        "type": "bbox",
                        "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
                        "query": "Gangnam-gu, Seoul, South Korea"
                    },
                    "network_options": {
                        "vehicle_types": ["passenger", "bus", "truck"],
                        "tls_guess": True,
                        "speed_limits": True,
                        "geometry_remove": True
                    },
                    "modifications": None,
                    "created_at": "2026-05-07T12:00:00Z"
                }
            ]
        }


class NetworkArtifact(BaseModel):
    """
    도로망 산출물

    생성된 SUMO 도로망 파일
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    artifact_id: str = Field(
        ...,
        description="산출물 ID",
        examples=["net-20260507-001"]
    )

    request_id: str = Field(
        ...,
        description="요청 ID",
        examples=["netreq-20260507-001"]
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
        description="도로망 파일 URI",
        examples=["s3://agent-t-networks/exp-20260507-001/base-001/network.net.xml"]
    )

    file_format: Literal["net.xml"] = Field(
        default="net.xml",
        description="파일 포맷"
    )

    file_size_bytes: int = Field(
        ...,
        description="파일 크기 (bytes)",
        examples=[1024576]
    )

    statistics: dict = Field(
        ...,
        description="도로망 통계",
        examples=[{
            "nodes": 1234,
            "edges": 2345,
            "junctions": 456,
            "traffic_lights": 78,
            "total_length_km": 45.6
        }]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시각"
    )

    generated_by: Optional[str] = Field(
        default=None,
        description="생성 도구",
        examples=["netconvert-1.18.0"]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "artifact_id": "net-20260507-001",
                    "request_id": "netreq-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "variant_id": "base-001",
                    "uri": "s3://agent-t-networks/exp-20260507-001/base-001/network.net.xml",
                    "file_format": "net.xml",
                    "file_size_bytes": 1024576,
                    "statistics": {
                        "nodes": 1234,
                        "edges": 2345,
                        "junctions": 456,
                        "traffic_lights": 78,
                        "total_length_km": 45.6,
                        "avg_edge_length_m": 19.4
                    },
                    "created_at": "2026-05-07T12:05:00Z",
                    "generated_by": "netconvert-1.18.0"
                }
            ]
        }
