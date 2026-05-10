"""
Kubernetes Job Executor (Placeholder)

Kubernetes Job으로 SUMO 실행 (향후 구현)
"""

from .executor import SumoExecutor, ExecutionResult


class KubernetesJobExecutor(SumoExecutor):
    """
    Kubernetes Job Executor (Placeholder)

    향후 구현:
    - Job manifest 생성
    - Job 실행 및 모니터링
    - 출력 파일 수집 (PVC 또는 S3)
    - Job 정리
    """

    def __init__(self, namespace: str = "agent-t"):
        self.namespace = namespace

    async def execute(
        self,
        config_file_path: str,
        working_directory: str,
    ) -> ExecutionResult:
        raise NotImplementedError(
            "KubernetesJobExecutor is not yet implemented. "
            "Use DryRunSumoExecutor or LocalSumoExecutor for now."
        )

    def validate_environment(self) -> tuple[bool, str]:
        return False, "KubernetesJobExecutor not implemented"
