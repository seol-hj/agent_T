"""
Report Schema

정책 리포트 생성 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ReportSection(BaseModel):
    """
    리포트 섹션

    리포트 내 개별 섹션
    """

    section_id: str = Field(
        ...,
        description="섹션 ID",
        examples=["executive-summary"]
    )

    title: str = Field(
        ...,
        description="섹션 제목",
        examples=["경영진 요약"]
    )

    content: str = Field(
        ...,
        description="섹션 내용 (마크다운 형식)",
        examples=["## 주요 발견사항\n\n- 통행 시간 16.1% 단축\n- 배출량 15.0% 감소"]
    )

    order: int = Field(
        ...,
        description="섹션 순서",
        examples=[1]
    )

    visualizations: Optional[list[dict]] = Field(
        default=None,
        description="시각화 자료 목록",
        examples=[[{
            "type": "bar_chart",
            "title": "시나리오별 평균 통행 시간",
            "data_uri": "s3://agent-t-reports/exp-20260507-001/chart-trip-duration.png"
        }]]
    )


class ReportArtifact(BaseModel):
    """
    리포트 산출물

    정책 의사결정을 위한 최종 리포트
    """

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전"
    )

    artifact_id: str = Field(
        ...,
        description="산출물 ID",
        examples=["rep-20260507-001"]
    )

    experiment_id: str = Field(
        ...,
        description="실험 ID",
        examples=["exp-20260507-001"]
    )

    analysis_id: str = Field(
        ...,
        description="분석 ID",
        examples=["ana-20260507-001"]
    )

    title: str = Field(
        ...,
        description="리포트 제목",
        examples=["강남구 출퇴근 시간대 신호등 최적화 효과 분석 보고서"]
    )

    uri: str = Field(
        ...,
        description="리포트 파일 URI",
        examples=["s3://agent-t-reports/exp-20260507-001/report.pdf"]
    )

    file_format: Literal["pdf", "markdown", "html"] = Field(
        ...,
        description="파일 포맷"
    )

    sections: list[ReportSection] = Field(
        ...,
        description="리포트 섹션 목록"
    )

    executive_summary: str = Field(
        ...,
        description="경영진 요약",
        examples=["신호 체계 최적화를 통해 평균 통행 시간 16.1%, 배출량 15.0% 감소 가능"]
    )

    recommendations: list[str] = Field(
        ...,
        description="권장사항 목록",
        examples=[["신호 주기를 120초에서 90초로 단축", "녹색 시간을 50초로 조정"]]
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
            "prompt_version": "report-gen-v2.0"
        }]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "schema_version": "1.0",
                    "artifact_id": "rep-20260507-001",
                    "experiment_id": "exp-20260507-001",
                    "analysis_id": "ana-20260507-001",
                    "title": "강남구 출퇴근 시간대 신호등 최적화 효과 분석 보고서",
                    "uri": "s3://agent-t-reports/exp-20260507-001/report.pdf",
                    "file_format": "pdf",
                    "sections": [
                        {
                            "section_id": "executive-summary",
                            "title": "경영진 요약",
                            "content": "## 주요 발견사항\n\n- 통행 시간 16.1% 단축\n- 배출량 15.0% 감소\n- 대기 시간 29.8% 개선",
                            "order": 1,
                            "visualizations": None
                        },
                        {
                            "section_id": "methodology",
                            "title": "분석 방법론",
                            "content": "## 실험 설계\n\nSUMO 시뮬레이터를 활용하여 강남구 출퇴근 시간대(07:00-09:00) 교통 상황을 재현하였습니다.",
                            "order": 2,
                            "visualizations": None
                        },
                        {
                            "section_id": "results",
                            "title": "분석 결과",
                            "content": "## 시나리오 비교\n\nBaseline 대비 Alternative 시나리오에서 모든 KPI가 개선되었습니다.",
                            "order": 3,
                            "visualizations": [
                                {
                                    "type": "bar_chart",
                                    "title": "시나리오별 평균 통행 시간",
                                    "data_uri": "s3://agent-t-reports/exp-20260507-001/chart-trip-duration.png"
                                },
                                {
                                    "type": "line_chart",
                                    "title": "시간대별 대기 시간 추이",
                                    "data_uri": "s3://agent-t-reports/exp-20260507-001/chart-waiting-time.png"
                                }
                            ]
                        },
                        {
                            "section_id": "recommendations",
                            "title": "권장사항",
                            "content": "## 정책 제안\n\n1. 신호 주기 단축\n2. 녹색 시간 조정\n3. 단계적 적용 계획",
                            "order": 4,
                            "visualizations": None
                        }
                    ],
                    "executive_summary": "신호 체계 최적화를 통해 평균 통행 시간 16.1%, 배출량 15.0% 감소 가능. 출퇴근 시간대 교통 혼잡 완화 및 환경 개선 효과 기대.",
                    "recommendations": [
                        "신호 주기를 120초에서 90초로 단축",
                        "녹색 시간을 50초로 조정",
                        "3개월 시범 운영 후 전체 확대 적용",
                        "실시간 모니터링 시스템 구축"
                    ],
                    "created_at": "2026-05-07T12:35:00Z",
                    "generated_by": {
                        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                        "provider": "bedrock",
                        "prompt_version": "report-gen-v2.0",
                        "latency_ms": 3450.2
                    }
                }
            ]
        }
