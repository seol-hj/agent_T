"""
Observability 사용 예제
"""

import asyncio
import time
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from common.observability import (
    configure_logging,
    get_logger,
    with_context,
    get_metrics_collector,
    Timer,
    LLMMetricsLogger,
    PipelineMetricsLogger,
)

# 로깅 설정
configure_logging(level="INFO", format_type="json")

logger = get_logger(__name__)


def example_basic_logging():
    """기본 로깅 예제"""
    print("\n" + "=" * 80)
    print("1. 기본 로깅")
    print("=" * 80)

    logger.info("Basic log message")
    logger.warning("Warning message", extra_fields={"severity": "medium"})
    logger.error("Error message", extra_fields={"error_code": 500})


def example_context_tracking():
    """컨텍스트 추적 예제"""
    print("\n" + "=" * 80)
    print("2. 컨텍스트 추적")
    print("=" * 80)

    with with_context(experiment_id="exp_001", step_name="orchestrator"):
        logger.info("Processing in orchestrator")

        # 중첩된 컨텍스트
        with with_context(step_name="scenario_builder"):
            logger.info("Processing in scenario_builder")


def example_metrics():
    """메트릭 수집 예제"""
    print("\n" + "=" * 80)
    print("3. 메트릭 수집")
    print("=" * 80)

    metrics = get_metrics_collector()

    # Counter
    metrics.record_counter("requests_total", value=1.0, labels={"status": "success"})
    logger.info("Counter recorded")

    # Gauge
    metrics.record_gauge("active_connections", value=42.0)
    logger.info("Gauge recorded")

    # Histogram (Latency)
    metrics.record_histogram("request_duration_seconds", value=0.123)
    logger.info("Histogram recorded")

    # Timer
    with Timer("processing_time"):
        time.sleep(0.1)
    logger.info("Timer recorded")


def example_llm_metrics():
    """LLM 메트릭 예제"""
    print("\n" + "=" * 80)
    print("4. LLM 메트릭")
    print("=" * 80)

    llm_logger = LLMMetricsLogger()

    with llm_logger.track_call(model="claude-3-sonnet", provider="bedrock"):
        # LLM 호출 시뮬레이션
        time.sleep(0.2)

        # 토큰 기록
        llm_logger.record_tokens(
            prompt_tokens=1000,
            completion_tokens=500
        )

        # 비용 기록
        llm_logger.record_cost(0.0045)

    logger.info("LLM metrics recorded")


def example_pipeline_metrics():
    """Pipeline 메트릭 예제"""
    print("\n" + "=" * 80)
    print("5. Pipeline 메트릭")
    print("=" * 80)

    pipeline_logger = PipelineMetricsLogger(
        experiment_id="exp_001",
        pipeline_type="e2e"
    )

    # 단계 1
    with pipeline_logger.track_step("orchestrator") as step:
        time.sleep(0.1)
        step.set_artifact("s3://bucket/spec.json")

    # 단계 2
    with pipeline_logger.track_step("scenario_builder") as step:
        time.sleep(0.15)
        step.set_artifact("s3://bucket/plan.json")

    # 완료
    pipeline_logger.finalize(
        status="completed",
        report_uri="s3://bucket/report.md"
    )

    logger.info("Pipeline metrics recorded")


def example_error_logging():
    """에러 로깅 예제"""
    print("\n" + "=" * 80)
    print("6. 에러 로깅")
    print("=" * 80)

    with with_context(experiment_id="exp_error", step_name="orchestrator"):
        try:
            # 의도적 에러
            result = 1 / 0
        except ZeroDivisionError as e:
            logger.error(
                "Division by zero",
                extra_fields={
                    "operation": "division",
                    "error_type": type(e).__name__,
                },
                exc_info=True  # 스택 트레이스 포함
            )


async def example_async_context():
    """비동기 컨텍스트 예제"""
    print("\n" + "=" * 80)
    print("7. 비동기 컨텍스트")
    print("=" * 80)

    with with_context(experiment_id="exp_async", step_name="async_process"):
        logger.info("Async process started")
        await asyncio.sleep(0.1)
        logger.info("Async process completed")


def main():
    """모든 예제 실행"""
    print("=" * 80)
    print("Observability Usage Examples")
    print("=" * 80)

    example_basic_logging()
    example_context_tracking()
    example_metrics()
    example_llm_metrics()
    example_pipeline_metrics()
    example_error_logging()

    # 비동기 예제
    asyncio.run(example_async_context())

    print("\n" + "=" * 80)
    print("All examples completed")
    print("=" * 80)


if __name__ == "__main__":
    main()
