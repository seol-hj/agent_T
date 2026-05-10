"""
Simulation Runner Service

시뮬레이션 실행 전체 흐름 관리
"""

import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas import SimulationRunRequest, SimulationRunArtifact
from common.gateways.storage import StorageGateway

from ..executors.executor import SumoExecutor
from .config_generator import SumoConfigGenerator
from .command_builder import SumoCommandBuilder


class SimulationRunnerService:
    """
    Simulation Runner 서비스

    SimulationRunRequest → SUMO 실행 → SimulationRunArtifact
    """

    def __init__(
        self,
        storage_gateway: StorageGateway,
        executor: SumoExecutor,
    ):
        """
        Args:
            storage_gateway: 스토리지 Gateway
            executor: SUMO Executor
        """
        self.storage = storage_gateway
        self.executor = executor
        self.config_generator = SumoConfigGenerator()
        self.command_builder = SumoCommandBuilder()

    async def run_simulation(
        self,
        request: dict,
    ) -> dict:
        """
        시뮬레이션 실행

        Args:
            request: SimulationRunRequest JSON

        Returns:
            SimulationRunArtifact JSON
        """
        start_time = time.time()

        # 1. Request 파싱
        experiment_id = request["experiment_id"]
        variant_id = request["variant_id"]
        request_id = request["request_id"]
        network_artifact = request["network_artifact"]
        demand_artifact = request["demand_artifact"]
        simulation_settings = request.get("simulation_settings", {})

        # 2. 임시 작업 디렉토리 생성
        work_dir = self._create_working_directory(experiment_id, variant_id)

        try:
            # 3. 입력 파일 다운로드
            network_file_path = await self._download_artifact(
                network_artifact["uri"],
                work_dir / "network.net.xml"
            )

            route_file_path = await self._download_artifact(
                demand_artifact["uri"],
                work_dir / "routes.rou.xml"
            )

            # 4. .sumocfg 생성
            output_files = {
                "tripinfo": "tripinfo.xml",
                "summary": "summary.xml",
                "queue": "queue.xml",
                "emission": "emission.xml",
            }

            config_xml = self.config_generator.generate_config(
                network_file="network.net.xml",
                route_file="routes.rou.xml",
                output_files=output_files,
                simulation_settings=simulation_settings,
            )

            config_file_path = work_dir / "simulation.sumocfg"
            config_file_path.write_text(config_xml, encoding='utf-8')

            # 5. SUMO 실행
            exec_result = await self.executor.execute(
                config_file_path=str(config_file_path),
                working_directory=str(work_dir),
            )

            if not exec_result.success:
                # 실행 실패
                artifact = self._create_failure_artifact(
                    request_id=request_id,
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                    error_message=exec_result.error_message or "Simulation failed",
                    execution_time_ms=exec_result.execution_time_ms,
                )
                return artifact

            # 6. 출력 파일 업로드
            output_uris = await self._upload_output_files(
                exec_result.output_files,
                experiment_id,
                variant_id,
            )

            # 7. 통계 계산 (간단한 파일 크기 기반)
            statistics = self._calculate_statistics(exec_result.output_files)

            # 8. SimulationRunArtifact 생성
            artifact_id = f"sim-{experiment_id.split('-')[-1]}-{variant_id}"

            processing_time_ms = (time.time() - start_time) * 1000

            artifact = {
                "schema_version": "1.0",
                "artifact_id": artifact_id,
                "request_id": request_id,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "outputs": output_uris,
                "statistics": statistics,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "generated_by": "simulator-runner-v0.1.0",
                "execution_time_ms": exec_result.execution_time_ms,
            }

            print(f"Simulation completed in {processing_time_ms:.1f}ms (execution: {exec_result.execution_time_ms:.1f}ms)")

            return artifact

        finally:
            # 9. 임시 디렉토리 정리
            self._cleanup_working_directory(work_dir)

    def _create_working_directory(self, experiment_id: str, variant_id: str) -> Path:
        """임시 작업 디렉토리 생성"""
        temp_base = Path(tempfile.gettempdir()) / "sumo-runs"
        work_dir = temp_base / f"{experiment_id}_{variant_id}_{int(time.time() * 1000)}"
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    async def _download_artifact(self, uri: str, local_path: Path) -> Path:
        """
        아티팩트 다운로드

        Args:
            uri: 아티팩트 URI (s3:// 또는 local://)
            local_path: 로컬 저장 경로

        Returns:
            로컬 파일 경로
        """
        content = await self.storage.download(uri)
        local_path.write_bytes(content)
        return local_path

    async def _upload_output_files(
        self,
        output_files: dict[str, str],
        experiment_id: str,
        variant_id: str,
    ) -> dict[str, str]:
        """
        출력 파일 업로드

        Args:
            output_files: {output_type: local_file_path}
            experiment_id: 실험 ID
            variant_id: 변형 ID

        Returns:
            {output_type: uri}
        """
        output_uris = {}

        for output_type, local_path in output_files.items():
            file_path = Path(local_path)
            if not file_path.exists():
                continue

            # 업로드
            remote_path = f"{experiment_id}/{variant_id}/{file_path.name}"
            content = file_path.read_bytes()
            uri = await self.storage.upload(
                file_path=remote_path,
                content=content,
            )

            output_uris[output_type] = uri

        return output_uris

    def _calculate_statistics(self, output_files: dict[str, str]) -> dict:
        """
        출력 파일 통계 계산

        Args:
            output_files: {output_type: local_file_path}

        Returns:
            통계 dict
        """
        stats = {}

        for output_type, local_path in output_files.items():
            file_path = Path(local_path)
            if file_path.exists():
                stats[f"{output_type}_size_bytes"] = file_path.stat().st_size

        return stats

    def _create_failure_artifact(
        self,
        request_id: str,
        experiment_id: str,
        variant_id: str,
        error_message: str,
        execution_time_ms: float,
    ) -> dict:
        """실패 아티팩트 생성"""
        artifact_id = f"sim-{experiment_id.split('-')[-1]}-{variant_id}"

        return {
            "schema_version": "1.0",
            "artifact_id": artifact_id,
            "request_id": request_id,
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "outputs": {},
            "statistics": {},
            "status": "failed",
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "simulator-runner-v0.1.0",
            "execution_time_ms": execution_time_ms,
            "error_message": error_message,
        }

    def _cleanup_working_directory(self, work_dir: Path):
        """작업 디렉토리 정리"""
        try:
            if work_dir.exists():
                shutil.rmtree(work_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup working directory {work_dir}: {e}")
