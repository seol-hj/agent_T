"""
Simulation Execution Gateway
시뮬레이션 실행 Provider 추상화 계층
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import uuid


@dataclass
class SimulationResult:
    """시뮬레이션 실행 결과"""
    simulation_id: str
    status: str  # queued, running, completed, failed
    executor: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    output_files: Dict[str, str] = None  # {파일명: 경로/URL}
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "simulation_id": self.simulation_id,
            "status": self.status,
            "executor": self.executor,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "output_files": self.output_files,
            "error": self.error,
            "metadata": self.metadata,
        }


class SimulationExecutionGateway(ABC):
    """
    Simulation Execution Gateway Base Class

    SUMO 시뮬레이션 실행 방식 추상화
    - DryRun: 실행 없이 검증만
    - Local: 로컬 SUMO 실행
    - Kubernetes: Job으로 실행
    """

    @abstractmethod
    async def execute(
        self,
        scenario_config: Dict[str, Any],
        network_file: str,
        route_file: str,
        output_dir: str,
        **kwargs
    ) -> SimulationResult:
        """
        시뮬레이션 실행

        Args:
            scenario_config: 시나리오 설정
            network_file: 도로망 파일 경로
            route_file: 경로 파일 경로
            output_dir: 출력 디렉토리
            **kwargs: 추가 파라미터

        Returns:
            SimulationResult: 실행 결과
        """
        pass

    @abstractmethod
    async def get_status(self, simulation_id: str) -> SimulationResult:
        """
        시뮬레이션 상태 조회

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            SimulationResult: 현재 상태
        """
        pass

    @abstractmethod
    async def cancel(self, simulation_id: str) -> bool:
        """
        시뮬레이션 취소

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            bool: 성공 여부
        """
        pass

    @property
    @abstractmethod
    def executor_name(self) -> str:
        """Executor 이름"""
        pass


# ============================================================================
# DryRun Executor
# ============================================================================

class DryRunExecutor(SimulationExecutionGateway):
    """
    DryRun Executor

    실제 시뮬레이션을 실행하지 않고 검증만 수행
    테스트 및 개발 환경용
    """

    def __init__(self, **kwargs):
        self.simulations: Dict[str, SimulationResult] = {}

    @property
    def executor_name(self) -> str:
        return "dryrun"

    async def execute(
        self,
        scenario_config: Dict[str, Any],
        network_file: str,
        route_file: str,
        output_dir: str,
        **kwargs
    ) -> SimulationResult:
        """DryRun 실행 (즉시 완료)"""
        simulation_id = f"sim-dryrun-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        result = SimulationResult(
            simulation_id=simulation_id,
            status="completed",
            executor=self.executor_name,
            started_at=now,
            completed_at=now,
            duration_seconds=0.1,
            output_files={
                "tripinfo.xml": f"{output_dir}/tripinfo.xml",
                "summary.xml": f"{output_dir}/summary.xml",
            },
            metadata={
                "scenario_config": scenario_config,
                "network_file": network_file,
                "route_file": route_file,
                "note": "DryRun - 실제 시뮬레이션 미실행",
            },
        )

        self.simulations[simulation_id] = result
        return result

    async def get_status(self, simulation_id: str) -> SimulationResult:
        """상태 조회"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation not found: {simulation_id}")
        return self.simulations[simulation_id]

    async def cancel(self, simulation_id: str) -> bool:
        """취소 (DryRun은 즉시 완료되므로 취소 불가)"""
        return False


# ============================================================================
# Local SUMO Executor
# ============================================================================

class LocalSumoExecutor(SimulationExecutionGateway):
    """
    Local SUMO Executor

    로컬 머신에서 SUMO 실행
    SUMO가 설치되어 있어야 함
    """

    def __init__(self, sumo_home: Optional[str] = None, **kwargs):
        self.sumo_home = sumo_home or os.getenv("SUMO_HOME")
        if not self.sumo_home:
            raise ValueError("SUMO_HOME is not set")

        self.simulations: Dict[str, SimulationResult] = {}

    @property
    def executor_name(self) -> str:
        return "local_sumo"

    async def execute(
        self,
        scenario_config: Dict[str, Any],
        network_file: str,
        route_file: str,
        output_dir: str,
        **kwargs
    ) -> SimulationResult:
        """로컬 SUMO 실행"""
        import subprocess
        from pathlib import Path

        simulation_id = f"sim-local-{uuid.uuid4().hex[:8]}"
        started_at = datetime.utcnow()

        # 출력 디렉토리 생성
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # SUMO 설정 파일 생성
        config_file = output_path / "simulation.sumocfg"
        self._create_sumo_config(
            config_file,
            network_file,
            route_file,
            output_path,
        )

        # 초기 상태 저장
        result = SimulationResult(
            simulation_id=simulation_id,
            status="running",
            executor=self.executor_name,
            started_at=started_at,
            metadata={
                "scenario_config": scenario_config,
                "config_file": str(config_file),
            },
        )
        self.simulations[simulation_id] = result

        try:
            # SUMO 실행
            sumo_binary = os.path.join(self.sumo_home, "bin", "sumo")
            cmd = [
                sumo_binary,
                "-c", str(config_file),
                "--no-warnings",
                "--no-step-log",
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300),  # 5분 타임아웃
            )

            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()

            if process.returncode == 0:
                # 성공
                result.status = "completed"
                result.completed_at = completed_at
                result.duration_seconds = duration
                result.output_files = {
                    "tripinfo.xml": str(output_path / "tripinfo.xml"),
                    "summary.xml": str(output_path / "summary.xml"),
                }
            else:
                # 실패
                result.status = "failed"
                result.completed_at = completed_at
                result.duration_seconds = duration
                result.error = process.stderr

        except subprocess.TimeoutExpired:
            result.status = "failed"
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (result.completed_at - started_at).total_seconds()
            result.error = "Simulation timeout"

        except Exception as e:
            result.status = "failed"
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (result.completed_at - started_at).total_seconds()
            result.error = str(e)

        self.simulations[simulation_id] = result
        return result

    def _create_sumo_config(
        self,
        config_file: Path,
        network_file: str,
        route_file: str,
        output_path: Path,
    ):
        """SUMO 설정 파일 생성"""
        config_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{network_file}"/>
        <route-files value="{route_file}"/>
    </input>
    <output>
        <tripinfo-output value="{output_path}/tripinfo.xml"/>
        <summary-output value="{output_path}/summary.xml"/>
    </output>
    <time>
        <begin value="0"/>
        <end value="3600"/>
    </time>
</configuration>
"""
        config_file.write_text(config_content)

    async def get_status(self, simulation_id: str) -> SimulationResult:
        """상태 조회"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation not found: {simulation_id}")
        return self.simulations[simulation_id]

    async def cancel(self, simulation_id: str) -> bool:
        """취소 (로컬 실행은 취소 불가 - 이미 완료됨)"""
        return False


# ============================================================================
# Kubernetes Job Executor (Placeholder)
# ============================================================================

class KubernetesJobExecutor(SimulationExecutionGateway):
    """
    Kubernetes Job Executor (Placeholder)

    Kubernetes Job으로 시뮬레이션 실행
    확장성 및 격리를 위해 사용
    향후 구현
    """

    def __init__(self, namespace: str = "default", **kwargs):
        self.namespace = namespace
        self.image = kwargs.get("image", "agent-t/simulation-worker:latest")

    @property
    def executor_name(self) -> str:
        return "k8s_job"

    async def execute(
        self,
        scenario_config: Dict[str, Any],
        network_file: str,
        route_file: str,
        output_dir: str,
        **kwargs
    ) -> SimulationResult:
        raise NotImplementedError("KubernetesJobExecutor is not implemented yet")

    async def get_status(self, simulation_id: str) -> SimulationResult:
        raise NotImplementedError("KubernetesJobExecutor is not implemented yet")

    async def cancel(self, simulation_id: str) -> bool:
        raise NotImplementedError("KubernetesJobExecutor is not implemented yet")


# ============================================================================
# Factory Function
# ============================================================================

def get_simulation_gateway(
    executor: Optional[str] = None,
    **kwargs
) -> SimulationExecutionGateway:
    """
    Simulation Execution Gateway Factory

    환경 변수:
        SIMULATION_EXECUTOR: dryrun | local_sumo | k8s_job (기본: dryrun)
        SUMO_HOME: SUMO 설치 경로 (local_sumo)

    Args:
        executor: Executor 이름
        **kwargs: 추가 설정

    Returns:
        SimulationExecutionGateway: 선택된 Executor

    Example:
        >>> executor = get_simulation_gateway()
        >>> result = await executor.execute(config, net, route, output)
    """
    executor = executor or os.getenv("SIMULATION_EXECUTOR", "dryrun")
    executor = executor.lower()

    if executor == "dryrun":
        return DryRunExecutor(**kwargs)

    elif executor == "local_sumo":
        return LocalSumoExecutor(**kwargs)

    elif executor == "k8s_job":
        return KubernetesJobExecutor(**kwargs)

    else:
        raise ValueError(f"Unknown simulation executor: {executor}")
