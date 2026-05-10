"""
Local SUMO Executor

로컬 환경에서 SUMO CLI 실행
"""

import asyncio
import time
import shutil
from pathlib import Path
from typing import Optional

from .executor import SumoExecutor, ExecutionResult


class LocalSumoExecutor(SumoExecutor):
    """
    Local SUMO Executor

    로컬에 설치된 SUMO를 subprocess로 실행
    """

    def __init__(
        self,
        sumo_binary: str = "sumo",
        timeout_seconds: int = 300,
    ):
        """
        Args:
            sumo_binary: SUMO 바이너리 경로 (기본: "sumo")
            timeout_seconds: 실행 타임아웃 (초)
        """
        self.sumo_binary = sumo_binary
        self.timeout_seconds = timeout_seconds

    async def execute(
        self,
        config_file_path: str,
        working_directory: str,
    ) -> ExecutionResult:
        """로컬 SUMO 실행"""
        start_time = time.time()

        # 환경 검증
        is_valid, message = self.validate_environment()
        if not is_valid:
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=message,
                execution_time_ms=0,
                output_files={},
                error_message=message,
            )

        # SUMO 명령 실행
        try:
            cmd = [self.sumo_binary, "-c", config_file_path]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )

            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            return_code = process.returncode

            execution_time_ms = (time.time() - start_time) * 1000

            # 출력 파일 수집
            output_files = self._collect_output_files(working_directory)

            success = return_code == 0
            error_message = stderr if not success else None

            return ExecutionResult(
                success=success,
                return_code=return_code,
                stdout=stdout,
                stderr=stderr,
                execution_time_ms=execution_time_ms,
                output_files=output_files,
                error_message=error_message,
            )

        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"SUMO execution timed out after {self.timeout_seconds}s",
                execution_time_ms=execution_time_ms,
                output_files={},
                error_message="Execution timeout",
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
                execution_time_ms=execution_time_ms,
                output_files={},
                error_message=f"Execution failed: {e}",
            )

    def validate_environment(self) -> tuple[bool, str]:
        """SUMO 설치 확인"""
        sumo_path = shutil.which(self.sumo_binary)
        if sumo_path is None:
            return False, f"SUMO binary '{self.sumo_binary}' not found in PATH"
        return True, f"SUMO found at {sumo_path}"

    def _collect_output_files(self, working_directory: str) -> dict[str, str]:
        """
        출력 파일 수집

        Args:
            working_directory: 작업 디렉토리

        Returns:
            {output_type: file_path}
        """
        work_dir = Path(working_directory)
        output_files = {}

        # 예상 출력 파일
        expected_outputs = {
            "tripinfo": "tripinfo.xml",
            "summary": "summary.xml",
            "queue": "queue.xml",
            "emission": "emission.xml",
        }

        for output_type, filename in expected_outputs.items():
            file_path = work_dir / filename
            if file_path.exists():
                output_files[output_type] = str(file_path)

        return output_files
