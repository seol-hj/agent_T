"""
Report Service

리포트 생성 전체 흐름 관리
"""

import time
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas import ReportRequest, ReportArtifact
from common.gateways.storage import StorageGateway

from ..reporters.reporter import Reporter


class ReportService:
    """
    리포트 서비스

    ReportRequest → 리포트 생성 → ReportArtifact
    """

    def __init__(
        self,
        storage_gateway: StorageGateway,
        reporter: Reporter,
    ):
        """
        Args:
            storage_gateway: 스토리지 Gateway
            reporter: Reporter 구현체
        """
        self.storage = storage_gateway
        self.reporter = reporter

    async def generate_report(
        self,
        request: dict,
    ) -> dict:
        """
        리포트 생성

        Args:
            request: ReportRequest JSON

        Returns:
            ReportArtifact JSON
        """
        start_time = time.time()

        # 1. Request 파싱
        experiment_id = request["experiment_id"]
        request_id = request["request_id"]
        analysis_result = request["analysis_result"]
        user_request = request.get("user_request")
        experiment_context = request.get("experiment_context")
        rag_contexts = request.get("rag_contexts")

        # 2. 리포트 생성
        report_content = await self.reporter.generate_report(
            analysis_result=analysis_result,
            user_request=user_request,
            experiment_context=experiment_context,
            rag_contexts=rag_contexts,
        )

        # 3. 스토리지에 저장
        markdown_uri = await self._upload_markdown(
            experiment_id=experiment_id,
            markdown=report_content.markdown,
        )

        pdf_uri = None
        if report_content.pdf:
            pdf_uri = await self._upload_pdf(
                experiment_id=experiment_id,
                pdf=report_content.pdf,
            )

        # 4. ReportArtifact 생성
        artifact_id = f"rep-{experiment_id.split('-')[-1]}"

        processing_time_ms = (time.time() - start_time) * 1000

        artifact = {
            "schema_version": "1.0",
            "artifact_id": artifact_id,
            "request_id": request_id,
            "experiment_id": experiment_id,
            "report_uri": markdown_uri,
            "report_format": "markdown",
            "pdf_uri": pdf_uri,
            "sections": self._extract_sections(),
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": f"reporter-{self.reporter.__class__.__name__.lower()}-v0.1.0",
            "processing_time_ms": processing_time_ms,
        }

        print(f"Report generated in {processing_time_ms:.1f}ms: {markdown_uri}")

        return artifact

    async def _upload_markdown(self, experiment_id: str, markdown: str) -> str:
        """
        Markdown 업로드

        Args:
            experiment_id: 실험 ID
            markdown: Markdown 문자열

        Returns:
            URI
        """
        file_path = f"{experiment_id}/report.md"
        content = markdown.encode('utf-8')
        uri = await self.storage.upload(
            file_path=file_path,
            content=content,
        )
        return uri

    async def _upload_pdf(self, experiment_id: str, pdf: bytes) -> str:
        """
        PDF 업로드

        Args:
            experiment_id: 실험 ID
            pdf: PDF 바이트

        Returns:
            URI
        """
        file_path = f"{experiment_id}/report.pdf"
        uri = await self.storage.upload(
            file_path=file_path,
            content=pdf,
        )
        return uri

    def _extract_sections(self) -> list[str]:
        """리포트 섹션 목록 추출"""
        return [
            "요약",
            "사용자 요청",
            "실험 조건",
            "기준 시나리오 결과",
            "대안 시나리오 결과",
            "개선율",
            "정책적 해석",
            "제한사항",
            "후속 검토 사항",
        ]
