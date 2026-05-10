"""
LLM Response Models
LLM 호출 결과 데이터 모델
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class LLMUsageMetadata:
    """LLM 사용량 메타데이터"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """
    LLM 호출 결과

    모든 LLM Provider는 이 포맷으로 응답을 반환한다.
    추적 및 디버깅을 위한 메타데이터를 포함한다.
    """

    # 응답 내용
    content: str

    # 추적 메타데이터 (필수)
    model_id: str
    provider: str
    prompt_version: Optional[str] = None

    # 성능 메트릭
    latency_ms: float = 0.0

    # 사용량
    usage: Optional[LLMUsageMetadata] = None

    # 요청 메타데이터
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    # 추가 정보
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        """타임스탬프 자동 설정"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "content": self.content,
            "model_id": self.model_id,
            "provider": self.provider,
            "prompt_version": self.prompt_version,
            "latency_ms": self.latency_ms,
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens if self.usage else 0,
                "completion_tokens": self.usage.completion_tokens if self.usage else 0,
                "total_tokens": self.usage.total_tokens if self.usage else 0,
            } if self.usage else None,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "error": self.error,
        }

    @property
    def success(self) -> bool:
        """성공 여부"""
        return self.error is None

    @property
    def total_tokens(self) -> int:
        """총 토큰 수"""
        return self.usage.total_tokens if self.usage else 0
