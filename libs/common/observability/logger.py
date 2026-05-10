"""
구조화된 로깅

JSON 포맷 로그 + 컨텍스트 자동 포함
"""

import logging
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime

from .context import get_context


class StructuredFormatter(logging.Formatter):
    """
    구조화된 JSON 로그 포맷터

    모든 로그를 JSON으로 출력하여 CloudWatch/OpenSearch에서 쉽게 파싱
    """

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 변환"""

        # 기본 필드
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 컨텍스트 추가 (request_id, experiment_id 등)
        context = get_context()
        if context:
            log_data["context"] = context.to_dict()

        # 예외 정보
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # 추가 필드 (extra 파라미터)
        if hasattr(record, "extra_fields"):
            log_data["extra"] = record.extra_fields

        return json.dumps(log_data, ensure_ascii=False)


class ContextAdapter(logging.LoggerAdapter):
    """
    컨텍스트를 자동으로 추가하는 Logger Adapter

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing request", extra_fields={"status": "started"})
    """

    def process(self, msg, kwargs):
        """로그 메시지 처리"""

        # extra_fields를 LogRecord에 추가
        if "extra" in kwargs:
            extra_fields = kwargs.pop("extra")
            if "extra" not in kwargs:
                kwargs["extra"] = {}
            kwargs["extra"]["extra_fields"] = extra_fields

        return msg, kwargs


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    enable_console: bool = True
):
    """
    로깅 설정

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 포맷 타입 ("json" 또는 "text")
        enable_console: 콘솔 출력 활성화
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        if format_type == "json":
            formatter = StructuredFormatter()
        else:
            # 텍스트 포맷 (로컬 개발용)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> ContextAdapter:
    """
    구조화된 로거 생성

    Args:
        name: 로거 이름 (보통 __name__)

    Returns:
        ContextAdapter

    Usage:
        logger = get_logger(__name__)
        logger.info("Starting process")
        logger.error("Failed to connect", extra_fields={"host": "localhost"})
    """
    base_logger = logging.getLogger(name)
    return ContextAdapter(base_logger, {})
