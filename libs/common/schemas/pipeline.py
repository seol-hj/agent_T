"""
Pipeline Schemas

E2E 파이프라인 실행 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class PipelineStepStatus(BaseModel):
    """파이프라인 단계 상태"""

    step_name: str = Field(..., description="단계 이름")
    status: Literal["pending", "running", "completed", "failed", "skipped"] = Field(
        ..., description="단계 상태"
    )
    started_at: Optional[str] = Field(None, description="시작 시간")
    completed_at: Optional[str] = Field(None, description="완료 시간")
    duration_ms: Optional[float] = Field(None, description="실행 시간 (ms)")
    artifact_uri: Optional[str] = Field(None, description="생성된 아티팩트 URI")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패 시)")


class PipelineExecutionRequest(BaseModel):
    """파이프라인 실행 요청"""

    schema_version: str = Field(default="1.0", description="스키마 버전")
    request_id: str = Field(..., description="요청 ID")
    user_request: str = Field(..., description="사용자 자연어 요청")
    dry_run: bool = Field(default=False, description="Dry Run 모드 (SUMO 실행 생략)")
    skip_steps: List[str] = Field(
        default_factory=list, description="건너뛸 단계 (테스트용)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "1.0",
                "request_id": "req-pipeline-001",
                "user_request": "교통 수요를 20% 증가시켰을 때 평균 통행 시간이 얼마나 변하는지 분석해주세요.",
                "dry_run": False,
                "skip_steps": [],
            }
        }


class PipelineExecutionResult(BaseModel):
    """파이프라인 실행 결과"""

    schema_version: str = Field(default="1.0", description="스키마 버전")
    execution_id: str = Field(..., description="실행 ID")
    request_id: str = Field(..., description="요청 ID")
    experiment_id: str = Field(..., description="실험 ID")
    status: Literal["completed", "failed", "partial"] = Field(..., description="전체 상태")
    steps: List[PipelineStepStatus] = Field(..., description="단계별 상태")
    report_uri: Optional[str] = Field(None, description="최종 리포트 URI")
    started_at: str = Field(..., description="시작 시간")
    completed_at: Optional[str] = Field(None, description="완료 시간")
    total_duration_ms: Optional[float] = Field(None, description="총 실행 시간 (ms)")
    error_message: Optional[str] = Field(None, description="전체 에러 메시지 (실패 시)")

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "1.0",
                "execution_id": "exec-001",
                "request_id": "req-pipeline-001",
                "experiment_id": "exp-001",
                "status": "completed",
                "steps": [
                    {
                        "step_name": "orchestrator",
                        "status": "completed",
                        "started_at": "2026-05-07T12:00:00",
                        "completed_at": "2026-05-07T12:00:02",
                        "duration_ms": 2000.0,
                    }
                ],
                "report_uri": "s3://bucket/exp-001/report.md",
                "started_at": "2026-05-07T12:00:00",
                "completed_at": "2026-05-07T12:05:00",
                "total_duration_ms": 300000.0,
            }
        }
