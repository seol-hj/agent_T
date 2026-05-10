"""
User Request Schema

사용자의 자연어 요구사항을 표현하는 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserRequest(BaseModel):
    """
    사용자 요구사항

    사용자가 자연어로 입력한 교통 시뮬레이션 요구사항
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    request_id: str = Field(
        ...,
        description="요청 고유 ID",
        examples=["req-20260507-123456"]
    )

    user_id: str = Field(
        ...,
        description="사용자 ID",
        examples=["user-001"]
    )

    raw_input: str = Field(
        ...,
        description="사용자가 입력한 원본 자연어 텍스트",
        examples=["서울 강남구 출퇴근 시간대 교통량을 분석하고 신호등 최적화 효과를 비교하고 싶습니다"]
    )

    language: str = Field(
        default="ko",
        description="입력 언어 (ISO 639-1)",
        examples=["ko", "en"]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="요청 생성 시각"
    )

    tags: Optional[list[str]] = Field(
        default=None,
        description="사용자 정의 태그",
        examples=[["교통신호", "강남구", "출퇴근"]]
    )

    context: Optional[dict] = Field(
        default=None,
        description="추가 컨텍스트 정보",
        examples=[{"previous_experiment_id": "exp-001"}]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "request_id": "req-20260507-123456",
                    "user_id": "user-001",
                    "raw_input": "서울 강남구 출퇴근 시간대 교통량을 분석하고 신호등 최적화 효과를 비교하고 싶습니다",
                    "language": "ko",
                    "created_at": "2026-05-07T12:00:00Z",
                    "tags": ["교통신호", "강남구", "출퇴근"],
                    "context": {
                        "previous_experiment_id": "exp-001",
                        "user_preference": "detailed_report"
                    }
                }
            ]
        }
