"""
SUMO Executor Interface

SUMO 시뮬레이션 실행 추상화
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """SUMO 실행 결과"""

    success: bool
    return_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    output_files: dict[str, str]  # {output_type: file_path}
    error_message: Optional[str] = None


class SumoExecutor(ABC):
    """
    SUMO 실행기 인터페이스

    구현체:
    - DryRunSumoExecutor: 모의 실행 (테스트용)
    - LocalSumoExecutor: 로컬 SUMO 실행
    - KubernetesJobExecutor: K8s Job으로 실행 (향후)
    """

    @abstractmethod
    async def execute(
        self,
        config_file_path: str,
        working_directory: str,
    ) -> ExecutionResult:
        """
        SUMO 시뮬레이션 실행

        Args:
            config_file_path: .sumocfg 파일 경로
            working_directory: 작업 디렉토리

        Returns:
            ExecutionResult
        """
        pass

    @abstractmethod
    def validate_environment(self) -> tuple[bool, str]:
        """
        실행 환경 검증

        Returns:
            (is_valid, message)
        """
        pass
