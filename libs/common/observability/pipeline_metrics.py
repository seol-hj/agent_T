"""
Pipeline 메트릭 로깅

Pipeline 단계별 latency, 상태 기록
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .context import get_context
from .logger import get_logger
from .metrics import get_metrics_collector, Timer

logger = get_logger(__name__)


class PipelineStepStatus(str, Enum):
    """Pipeline 단계 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineStepMetrics:
    """Pipeline 단계 메트릭"""

    # 기본 정보
    step_name: str
    status: PipelineStepStatus

    # 타이밍
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None

    # 산출물
    artifact_uri: Optional[str] = None
    artifact_size_bytes: Optional[int] = None

    # 에러
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # 리소스
    cpu_usage: Optional[float] = None
    memory_usage_mb: Optional[float] = None

    # 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineExecutionMetrics:
    """Pipeline 전체 실행 메트릭"""

    # 기본 정보
    experiment_id: str
    pipeline_type: str  # e2e, network_only, etc.

    # 상태
    status: str  # completed, failed, partial

    # 타이밍
    started_at: str
    completed_at: Optional[str] = None
    total_duration_ms: Optional[float] = None

    # 단계별 메트릭
    steps: List[PipelineStepMetrics] = field(default_factory=list)

    # 산출물
    report_uri: Optional[str] = None

    # 에러
    error_message: Optional[str] = None

    # 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)


class PipelineMetricsLogger:
    """
    Pipeline 메트릭 로거

    Usage:
        logger = PipelineMetricsLogger(experiment_id="exp_001")

        with logger.track_step("orchestrator"):
            # process
            logger.set_artifact("s3://bucket/spec.json")

        logger.finalize(status="completed")
    """

    def __init__(self, experiment_id: str, pipeline_type: str = "e2e"):
        """
        Args:
            experiment_id: 실험 ID
            pipeline_type: 파이프라인 타입
        """
        self.experiment_id = experiment_id
        self.pipeline_type = pipeline_type
        self.started_at = datetime.utcnow().isoformat()
        self.steps: List[PipelineStepMetrics] = []
        self.current_step: Optional[PipelineStepMetrics] = None
        self.metrics_collector = get_metrics_collector()

    def track_step(self, step_name: str) -> "StepTracker":
        """
        단계 추적 시작

        Args:
            step_name: 단계 이름

        Returns:
            StepTracker (context manager)
        """
        return StepTracker(self, step_name)

    def _start_step(self, step_name: str):
        """단계 시작 (내부)"""
        step_metrics = PipelineStepMetrics(
            step_name=step_name,
            status=PipelineStepStatus.RUNNING,
            started_at=datetime.utcnow().isoformat(),
        )
        self.steps.append(step_metrics)
        self.current_step = step_metrics

        logger.info(
            f"Pipeline step started: {step_name}",
            extra_fields={"step_name": step_name}
        )

    def _complete_step(
        self,
        success: bool,
        error: Optional[Exception] = None,
        artifact_uri: Optional[str] = None
    ):
        """단계 완료 (내부)"""
        if self.current_step is None:
            return

        step = self.current_step
        step.completed_at = datetime.utcnow().isoformat()

        # Duration 계산
        if step.started_at:
            started = datetime.fromisoformat(step.started_at)
            completed = datetime.fromisoformat(step.completed_at)
            step.duration_ms = (completed - started).total_seconds() * 1000

        # 상태 설정
        if success:
            step.status = PipelineStepStatus.COMPLETED
        else:
            step.status = PipelineStepStatus.FAILED
            if error:
                step.error_message = str(error)
                step.error_type = type(error).__name__

        # Artifact 설정
        if artifact_uri:
            step.artifact_uri = artifact_uri

        # 로그
        logger.info(
            f"Pipeline step completed: {step.step_name}",
            extra_fields={
                "step_name": step.step_name,
                "status": step.status.value,
                "duration_ms": step.duration_ms,
                "artifact_uri": step.artifact_uri,
                "error": step.error_message,
            }
        )

        # Prometheus 메트릭
        if step.duration_ms:
            self.metrics_collector.record_histogram(
                name="pipeline_step_duration_seconds",
                value=step.duration_ms / 1000,
                labels={
                    "step": step.step_name,
                    "status": "success" if success else "error",
                }
            )

        self.current_step = None

    def set_artifact(self, artifact_uri: str, size_bytes: Optional[int] = None):
        """현재 단계의 artifact 설정"""
        if self.current_step:
            self.current_step.artifact_uri = artifact_uri
            self.current_step.artifact_size_bytes = size_bytes

    def set_metadata(self, **kwargs):
        """현재 단계의 메타데이터 설정"""
        if self.current_step:
            self.current_step.metadata.update(kwargs)

    def finalize(self, status: str, report_uri: Optional[str] = None, error: Optional[str] = None):
        """
        Pipeline 실행 완료

        Args:
            status: 전체 상태 (completed, failed, partial)
            report_uri: 최종 리포트 URI
            error: 에러 메시지
        """
        completed_at = datetime.utcnow().isoformat()
        started = datetime.fromisoformat(self.started_at)
        completed = datetime.fromisoformat(completed_at)
        total_duration_ms = (completed - started).total_seconds() * 1000

        metrics = PipelineExecutionMetrics(
            experiment_id=self.experiment_id,
            pipeline_type=self.pipeline_type,
            status=status,
            started_at=self.started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            steps=self.steps,
            report_uri=report_uri,
            error_message=error,
        )

        # 로그
        logger.info(
            "Pipeline execution completed",
            extra_fields={
                "experiment_id": self.experiment_id,
                "pipeline_type": self.pipeline_type,
                "status": status,
                "total_duration_ms": total_duration_ms,
                "total_steps": len(self.steps),
                "completed_steps": sum(1 for s in self.steps if s.status == PipelineStepStatus.COMPLETED),
                "failed_steps": sum(1 for s in self.steps if s.status == PipelineStepStatus.FAILED),
                "report_uri": report_uri,
                "error": error,
            }
        )

        # Prometheus 메트릭
        self.metrics_collector.record_histogram(
            name="pipeline_execution_duration_seconds",
            value=total_duration_ms / 1000,
            labels={
                "pipeline_type": self.pipeline_type,
                "status": status,
            }
        )

        self.metrics_collector.record_counter(
            name="pipeline_executions_total",
            value=1.0,
            labels={
                "pipeline_type": self.pipeline_type,
                "status": status,
            }
        )


class StepTracker:
    """
    단계 추적 context manager

    Usage:
        with logger.track_step("orchestrator"):
            # process
            pass
    """

    def __init__(self, logger: PipelineMetricsLogger, step_name: str):
        self.logger = logger
        self.step_name = step_name
        self.artifact_uri: Optional[str] = None

    def set_artifact(self, artifact_uri: str):
        """Artifact URI 설정"""
        self.artifact_uri = artifact_uri
        self.logger.set_artifact(artifact_uri)

    def set_metadata(self, **kwargs):
        """메타데이터 설정"""
        self.logger.set_metadata(**kwargs)

    def __enter__(self):
        """단계 시작"""
        self.logger._start_step(self.step_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """단계 완료"""
        success = exc_type is None
        self.logger._complete_step(
            success=success,
            error=exc_val if exc_val else None,
            artifact_uri=self.artifact_uri
        )
