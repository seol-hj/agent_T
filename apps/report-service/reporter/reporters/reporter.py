"""
Reporter Interface

리포트 생성 추상화
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ReportContent:
    """리포트 콘텐츠"""

    markdown: str
    pdf: Optional[bytes] = None


class Reporter(ABC):
    """
    Reporter 인터페이스

    구현체:
    - TemplateReporter: 템플릿 기반 리포트 생성
    - LLMReporter: LLM 기반 정책적 해석 리포트 생성
    """

    @abstractmethod
    async def generate_report(
        self,
        analysis_result: dict,
        user_request: Optional[str] = None,
        experiment_context: Optional[dict] = None,
        rag_contexts: Optional[list] = None,
    ) -> ReportContent:
        """
        리포트 생성

        Args:
            analysis_result: AnalysisResult JSON
            user_request: 사용자 원본 요청 (선택)
            experiment_context: 실험 컨텍스트 (선택)
            rag_contexts: RAG 컨텍스트 리스트 (선택)

        Returns:
            ReportContent (Markdown + PDF)
        """
        pass
