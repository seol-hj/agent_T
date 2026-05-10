"""
Parser Service

자연어 입력을 ExperimentSpec으로 변환하는 서비스
"""

import json
import time
from typing import Optional
from datetime import datetime
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.gateways.llm import LLMGateway
from common.schemas import ExperimentSpec

from ..models.parse_response import ParseResponse, RAGContext
from ..prompts.experiment_parser import (
    EXPERIMENT_PARSER_SYSTEM_PROMPT,
    build_experiment_parser_prompt,
    generate_clarification_question,
)


class ParserService:
    """
    자연어 → ExperimentSpec 파서 서비스
    """

    def __init__(self, llm_gateway: LLMGateway, max_retries: int = 3):
        """
        Args:
            llm_gateway: LLM Gateway 인스턴스
            max_retries: Pydantic 검증 실패 시 최대 재시도 횟수
        """
        self.llm = llm_gateway
        self.max_retries = max_retries

    async def parse_request(
        self,
        user_input: str,
        request_id: str,
        rag_contexts: Optional[list[RAGContext]] = None,
    ) -> ParseResponse:
        """
        사용자 자연어 입력을 ExperimentSpec으로 변환

        Args:
            user_input: 사용자 자연어 입력
            request_id: 요청 ID
            rag_contexts: RAG 컨텍스트 목록 (Optional)

        Returns:
            ParseResponse (성공/보완질문/오류)
        """
        start_time = time.time()

        try:
            # RAG 컨텍스트 조합
            rag_context_str = self._build_rag_context(rag_contexts) if rag_contexts else None

            # 프롬프트 생성
            prompt = build_experiment_parser_prompt(
                user_input=user_input,
                request_id=request_id,
                rag_context=rag_context_str,
            )

            # LLM 호출 (재시도 로직 포함)
            llm_response = None
            validation_error = None

            for attempt in range(self.max_retries):
                try:
                    llm_response = await self.llm.generate(
                        prompt=prompt,
                        system_prompt=EXPERIMENT_PARSER_SYSTEM_PROMPT,
                        temperature=0.3,
                        max_tokens=2000,
                        prompt_version="experiment-parser-v1.0",
                    )

                    if not llm_response.success:
                        raise Exception(f"LLM 호출 실패: {llm_response.error}")

                    # JSON 파싱
                    parsed_output = self._extract_json(llm_response.content)

                    # ExperimentSpec 검증 (있는 경우)
                    if parsed_output.get("experiment_spec"):
                        experiment_spec = ExperimentSpec(**parsed_output["experiment_spec"])
                        # 검증 성공
                        break
                    else:
                        # missing_fields가 있는 경우 — 검증 불필요
                        break

                except ValidationError as e:
                    validation_error = e
                    if attempt < self.max_retries - 1:
                        # 재시도: 검증 오류 피드백 추가
                        prompt += f"\n\n[이전 시도 검증 오류]\n{str(e)}\n\n위 오류를 수정하여 다시 생성하세요."
                        continue
                    else:
                        # 최대 재시도 초과
                        raise

            # 결과 처리
            processing_time_ms = (time.time() - start_time) * 1000

            request_type = parsed_output.get("request_type")
            confidence_score = parsed_output.get("confidence_score")
            experiment_spec_data = parsed_output.get("experiment_spec")
            missing_fields = parsed_output.get("missing_fields")

            # missing_fields가 있으면 보완 질문 생성
            if missing_fields:
                clarification = (
                    parsed_output.get("clarification_question")
                    or generate_clarification_question(missing_fields)
                )
                return ParseResponse(
                    status="needs_clarification",
                    experiment_spec=None,
                    missing_fields=missing_fields,
                    clarification_question=clarification,
                    request_type=request_type,
                    confidence_score=confidence_score,
                    processing_time_ms=processing_time_ms,
                    llm_metadata=self._extract_llm_metadata(llm_response),
                )

            # 성공
            return ParseResponse(
                status="success",
                experiment_spec=experiment_spec_data,
                missing_fields=None,
                clarification_question=None,
                request_type=request_type,
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms,
                llm_metadata=self._extract_llm_metadata(llm_response),
            )

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            return ParseResponse(
                status="error",
                experiment_spec=None,
                missing_fields=None,
                clarification_question=None,
                request_type=None,
                confidence_score=None,
                processing_time_ms=processing_time_ms,
                llm_metadata=None,
                error_message=str(e),
            )

    def _build_rag_context(self, rag_contexts: list[RAGContext]) -> str:
        """RAG 컨텍스트 목록을 문자열로 조합"""
        if not rag_contexts:
            return ""

        lines = []
        for ctx in rag_contexts:
            lines.append(f"[{ctx.context_type}] {ctx.content}")
            if ctx.source:
                lines.append(f"  (출처: {ctx.source})")
        return "\n".join(lines)

    def _extract_json(self, content: str) -> dict:
        """
        LLM 응답에서 JSON 추출

        ```json ... ``` 블록 또는 순수 JSON 파싱
        """
        content = content.strip()

        # ```json ... ``` 블록 제거
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        return json.loads(content)

    def _extract_llm_metadata(self, llm_response) -> dict:
        """LLM 응답에서 메타데이터 추출"""
        if not llm_response:
            return {}

        return {
            "model_id": llm_response.model_id,
            "provider": llm_response.provider,
            "prompt_version": llm_response.prompt_version,
            "latency_ms": llm_response.latency_ms,
            "input_tokens": llm_response.usage.input_tokens if llm_response.usage else None,
            "output_tokens": llm_response.usage.output_tokens if llm_response.usage else None,
        }


class AgentLogger:
    """
    Agent 로그 저장 서비스 (Placeholder)

    실제 구현에서는 DB 또는 로그 시스템에 저장
    """

    def __init__(self):
        self.logs = []

    async def log(
        self,
        level: str,
        agent_name: str,
        message: str,
        experiment_id: Optional[str] = None,
        request_id: Optional[str] = None,
        context: Optional[dict] = None,
        error_details: Optional[dict] = None,
        llm_metadata: Optional[dict] = None,
    ):
        """
        로그 저장 (현재는 메모리에만 저장)

        실제 구현에서는:
        - AgentLog 스키마 사용
        - PostgreSQL/CloudWatch Logs에 저장
        - 비동기 처리
        """
        log_entry = {
            "log_id": f"log-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{len(self.logs):03d}",
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "agent_name": agent_name,
            "experiment_id": experiment_id,
            "request_id": request_id,
            "message": message,
            "context": context,
            "error_details": error_details,
            "llm_metadata": llm_metadata,
        }
        self.logs.append(log_entry)
        # TODO: DB 저장 또는 로그 시스템 전송
        print(f"[LOG] [{level.upper()}] {agent_name}: {message}")
