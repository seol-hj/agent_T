"""
Observability Context

request_id, experiment_id, run_id 추적
"""

from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class ObservabilityContext:
    """
    관측성 컨텍스트

    모든 로그/메트릭에 포함될 추적 정보
    """
    request_id: str
    experiment_id: Optional[str] = None
    run_id: Optional[str] = None
    user_id: Optional[str] = None
    step_name: Optional[str] = None
    variant_id: Optional[str] = None

    # 타임스탬프
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # 추가 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "request_id": self.request_id,
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "user_id": self.user_id,
            "step_name": self.step_name,
            "variant_id": self.variant_id,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def copy(self, **updates) -> "ObservabilityContext":
        """컨텍스트 복사 및 업데이트"""
        data = self.to_dict()
        data.update(updates)
        return ObservabilityContext(**data)


# Thread-safe context variable
_context_var: ContextVar[Optional[ObservabilityContext]] = ContextVar(
    "observability_context", default=None
)


def set_context(context: ObservabilityContext):
    """컨텍스트 설정"""
    _context_var.set(context)


def get_context() -> Optional[ObservabilityContext]:
    """현재 컨텍스트 반환"""
    return _context_var.get()


def create_context(
    request_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    run_id: Optional[str] = None,
    **kwargs
) -> ObservabilityContext:
    """
    새 컨텍스트 생성

    Args:
        request_id: 요청 ID (자동 생성)
        experiment_id: 실험 ID
        run_id: 실행 ID
        **kwargs: 추가 필드

    Returns:
        ObservabilityContext
    """
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"

    return ObservabilityContext(
        request_id=request_id,
        experiment_id=experiment_id,
        run_id=run_id,
        **kwargs
    )


class with_context:
    """
    컨텍스트 매니저

    Usage:
        with with_context(experiment_id="exp_001"):
            logger.info("Processing experiment")
    """

    def __init__(self, **kwargs):
        """
        Args:
            **kwargs: 컨텍스트 필드 (request_id, experiment_id 등)
        """
        self.kwargs = kwargs
        self.previous_context: Optional[ObservabilityContext] = None
        self.new_context: Optional[ObservabilityContext] = None

    def __enter__(self):
        """컨텍스트 진입"""
        self.previous_context = get_context()

        if self.previous_context:
            # 기존 컨텍스트 복사 및 업데이트
            self.new_context = self.previous_context.copy(**self.kwargs)
        else:
            # 새 컨텍스트 생성
            self.new_context = create_context(**self.kwargs)

        set_context(self.new_context)
        return self.new_context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 종료"""
        set_context(self.previous_context)
