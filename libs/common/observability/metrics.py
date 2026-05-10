"""
메트릭 수집

Prometheus 형식 메트릭 (향후 확장)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import time

from .context import get_context
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class Metric:
    """메트릭 데이터"""
    name: str
    value: float
    metric_type: str  # counter, gauge, histogram, summary
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MetricsCollector:
    """
    메트릭 수집기

    현재는 로그로 출력, 향후 Prometheus exporter로 확장 가능
    """

    def __init__(self):
        self.metrics: list[Metric] = []

    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        카운터 메트릭 기록

        Args:
            name: 메트릭 이름
            value: 값 (기본: 1.0)
            labels: 레이블 (예: {"status": "success"})
        """
        self._record(name, value, "counter", labels or {})

    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        게이지 메트릭 기록

        Args:
            name: 메트릭 이름
            value: 값
            labels: 레이블
        """
        self._record(name, value, "gauge", labels or {})

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        히스토그램 메트릭 기록 (주로 latency)

        Args:
            name: 메트릭 이름
            value: 값 (초 단위)
            labels: 레이블
        """
        self._record(name, value, "histogram", labels or {})

    def _record(
        self,
        name: str,
        value: float,
        metric_type: str,
        labels: Dict[str, str]
    ):
        """메트릭 기록 (내부)"""

        # 컨텍스트에서 레이블 자동 추가
        context = get_context()
        if context:
            if context.experiment_id:
                labels["experiment_id"] = context.experiment_id
            if context.request_id:
                labels["request_id"] = context.request_id
            if context.step_name:
                labels["step"] = context.step_name

        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels
        )

        self.metrics.append(metric)

        # 로그로 출력 (향후 Prometheus exporter로 변경)
        logger.debug(
            f"Metric recorded: {name}",
            extra_fields={
                "metric_name": name,
                "metric_type": metric_type,
                "metric_value": value,
                "metric_labels": labels,
            }
        )

    def get_metrics(self) -> list[Metric]:
        """수집된 메트릭 반환"""
        return self.metrics

    def clear(self):
        """메트릭 초기화"""
        self.metrics.clear()


# Global 메트릭 수집기
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Global 메트릭 수집기 반환"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


class Timer:
    """
    실행 시간 측정

    Usage:
        with Timer("processing_time"):
            process_data()
    """

    def __init__(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """
        Args:
            metric_name: 메트릭 이름
            labels: 추가 레이블
        """
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time: Optional[float] = None
        self.collector = get_metrics_collector()

    def __enter__(self):
        """타이머 시작"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """타이머 종료 및 메트릭 기록"""
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time

        # 성공/실패 레이블 추가
        if exc_type is not None:
            self.labels["status"] = "error"
            self.labels["error_type"] = exc_type.__name__
        else:
            self.labels["status"] = "success"

        self.collector.record_histogram(
            name=self.metric_name,
            value=elapsed,
            labels=self.labels
        )

        logger.info(
            f"{self.metric_name} completed",
            extra_fields={
                "duration_seconds": elapsed,
                "labels": self.labels,
            }
        )
