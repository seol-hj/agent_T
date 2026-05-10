"""
LLM 메트릭 로깅

LLM 호출 latency, token 사용량, 비용 기록
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import time

from .context import get_context
from .logger import get_logger
from .metrics import get_metrics_collector

logger = get_logger(__name__)


@dataclass
class LLMCallMetrics:
    """LLM 호출 메트릭"""

    # 기본 정보
    model_name: str
    provider: str  # bedrock, openai, etc.
    operation: str  # completion, embedding, etc.

    # 타이밍
    latency_ms: float
    started_at: str
    completed_at: str

    # 토큰
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    # 비용 (USD)
    estimated_cost: Optional[float] = None

    # 응답 품질
    response_length: Optional[int] = None
    finish_reason: Optional[str] = None

    # 에러
    error: Optional[str] = None
    error_type: Optional[str] = None

    # 컨텍스트
    request_id: Optional[str] = None
    experiment_id: Optional[str] = None
    step_name: Optional[str] = None

    # 추가 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMMetricsLogger:
    """
    LLM 메트릭 로거

    Usage:
        logger = LLMMetricsLogger()
        with logger.track_call(model="claude-3-sonnet", provider="bedrock"):
            response = llm_client.generate(...)
            logger.record_tokens(response.usage)
    """

    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.start_time: Optional[float] = None
        self.model_name: Optional[str] = None
        self.provider: Optional[str] = None
        self.operation: Optional[str] = None
        self.prompt_tokens: Optional[int] = None
        self.completion_tokens: Optional[int] = None
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def track_call(
        self,
        model: str,
        provider: str,
        operation: str = "completion"
    ) -> "LLMMetricsLogger":
        """
        LLM 호출 추적 시작

        Args:
            model: 모델명 (claude-3-sonnet, gpt-4, etc.)
            provider: 제공자 (bedrock, openai, etc.)
            operation: 작업 타입 (completion, embedding, etc.)

        Returns:
            self (context manager용)
        """
        self.model_name = model
        self.provider = provider
        self.operation = operation
        self.start_time = time.time()
        return self

    def record_tokens(
        self,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None
    ):
        """
        토큰 사용량 기록

        Args:
            prompt_tokens: 프롬프트 토큰 수
            completion_tokens: 완성 토큰 수
            total_tokens: 총 토큰 수
        """
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

        if total_tokens is None and prompt_tokens and completion_tokens:
            total_tokens = prompt_tokens + completion_tokens

        # 메트릭 기록
        if total_tokens:
            self.metrics_collector.record_counter(
                name="llm_tokens_total",
                value=float(total_tokens),
                labels={
                    "model": self.model_name or "unknown",
                    "provider": self.provider or "unknown",
                }
            )

    def record_cost(self, cost: float):
        """
        비용 기록 (USD)

        Args:
            cost: 예상 비용 (달러)
        """
        self.metrics_collector.record_counter(
            name="llm_cost_usd",
            value=cost,
            labels={
                "model": self.model_name or "unknown",
                "provider": self.provider or "unknown",
            }
        )

    def record_error(self, error: Exception):
        """
        에러 기록

        Args:
            error: 예외 객체
        """
        self.error = str(error)

        self.metrics_collector.record_counter(
            name="llm_errors_total",
            value=1.0,
            labels={
                "model": self.model_name or "unknown",
                "provider": self.provider or "unknown",
                "error_type": type(error).__name__,
            }
        )

    def set_metadata(self, **kwargs):
        """추가 메타데이터 설정"""
        self.metadata.update(kwargs)

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 및 메트릭 기록"""
        if self.start_time is None:
            return

        # Latency 계산
        latency_ms = (time.time() - self.start_time) * 1000

        # 컨텍스트 가져오기
        context = get_context()

        # 에러 처리
        error = None
        error_type = None
        if exc_type is not None:
            error = str(exc_val)
            error_type = exc_type.__name__
            self.record_error(exc_val)

        # 메트릭 생성
        metrics = LLMCallMetrics(
            model_name=self.model_name or "unknown",
            provider=self.provider or "unknown",
            operation=self.operation or "completion",
            latency_ms=latency_ms,
            started_at=datetime.utcfromtimestamp(self.start_time).isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=(
                (self.prompt_tokens or 0) + (self.completion_tokens or 0)
                if self.prompt_tokens or self.completion_tokens
                else None
            ),
            error=error,
            error_type=error_type,
            request_id=context.request_id if context else None,
            experiment_id=context.experiment_id if context else None,
            step_name=context.step_name if context else None,
            metadata=self.metadata,
        )

        # 구조화된 로그
        logger.info(
            "LLM call completed",
            extra_fields={
                "llm_metrics": {
                    "model": metrics.model_name,
                    "provider": metrics.provider,
                    "operation": metrics.operation,
                    "latency_ms": metrics.latency_ms,
                    "prompt_tokens": metrics.prompt_tokens,
                    "completion_tokens": metrics.completion_tokens,
                    "total_tokens": metrics.total_tokens,
                    "estimated_cost": metrics.estimated_cost,
                    "error": metrics.error,
                }
            }
        )

        # Prometheus 메트릭
        self.metrics_collector.record_histogram(
            name="llm_call_latency_seconds",
            value=latency_ms / 1000,
            labels={
                "model": metrics.model_name,
                "provider": metrics.provider,
                "status": "error" if error else "success",
            }
        )


def calculate_bedrock_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> float:
    """
    Bedrock 비용 계산 (Placeholder)

    Args:
        model: 모델명
        prompt_tokens: 프롬프트 토큰 수
        completion_tokens: 완성 토큰 수

    Returns:
        예상 비용 (USD)
    """
    # Bedrock 가격 (2024년 기준, 예시)
    pricing = {
        "claude-3-sonnet": {
            "input": 0.003 / 1000,   # $0.003 per 1K tokens
            "output": 0.015 / 1000,  # $0.015 per 1K tokens
        },
        "claude-3-haiku": {
            "input": 0.00025 / 1000,
            "output": 0.00125 / 1000,
        },
        "claude-3-opus": {
            "input": 0.015 / 1000,
            "output": 0.075 / 1000,
        },
    }

    # 모델 매칭 (부분 매칭)
    model_lower = model.lower()
    for model_key, prices in pricing.items():
        if model_key in model_lower:
            input_cost = prompt_tokens * prices["input"]
            output_cost = completion_tokens * prices["output"]
            return input_cost + output_cost

    # 기본값 (알 수 없는 모델)
    return 0.0
