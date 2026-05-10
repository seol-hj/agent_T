"""
Pipeline Service

E2E 파이프라인 실행 서비스
"""

import time
import uuid
from datetime import datetime
from typing import Optional
import httpx

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas.pipeline import (
    PipelineExecutionRequest,
    PipelineExecutionResult,
    PipelineStepStatus,
)


class PipelineService:
    """
    파이프라인 실행 서비스

    전체 E2E 흐름 관리:
    1. Orchestrator
    2. Scenario Builder
    3. Network Builder
    4. Demand Builder
    5. Simulator Runner
    6. Analyzer
    7. Reporter
    """

    def __init__(
        self,
        orchestrator_url: str = "http://orchestrator:8001",
        scenario_builder_url: str = "http://scenario-builder:8002",
        network_builder_url: str = "http://network-builder:8003",
        demand_builder_url: str = "http://demand-builder:8004",
        simulator_runner_url: str = "http://simulator-runner:8005",
        analyzer_url: str = "http://analyzer:8006",
        reporter_url: str = "http://reporter:8007",
        timeout: float = 300.0,
    ):
        """
        Args:
            orchestrator_url: Orchestrator 서비스 URL
            scenario_builder_url: Scenario Builder 서비스 URL
            network_builder_url: Network Builder 서비스 URL
            demand_builder_url: Demand Builder 서비스 URL
            simulator_runner_url: Simulator Runner 서비스 URL
            analyzer_url: Analyzer 서비스 URL
            reporter_url: Reporter 서비스 URL
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.orchestrator_url = orchestrator_url
        self.scenario_builder_url = scenario_builder_url
        self.network_builder_url = network_builder_url
        self.demand_builder_url = demand_builder_url
        self.simulator_runner_url = simulator_runner_url
        self.analyzer_url = analyzer_url
        self.reporter_url = reporter_url
        self.timeout = timeout

    async def execute_pipeline(
        self,
        request: PipelineExecutionRequest,
    ) -> PipelineExecutionResult:
        """
        파이프라인 실행

        Args:
            request: 파이프라인 실행 요청

        Returns:
            파이프라인 실행 결과
        """
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        started_at = datetime.utcnow().isoformat()
        start_time = time.time()

        steps: list[PipelineStepStatus] = []

        # 실험 ID (Orchestrator에서 생성)
        experiment_id = None

        try:
            # 1. Orchestrator
            experiment_spec, orchestrator_step = await self._run_orchestrator(
                request, steps
            )
            steps.append(orchestrator_step)

            if orchestrator_step.status == "failed":
                return self._create_result(
                    execution_id, request.request_id, None, "failed", steps,
                    None, started_at, start_time, orchestrator_step.error_message
                )

            experiment_id = experiment_spec["experiment_id"]

            # 2. Scenario Builder
            scenario_plan, scenario_step = await self._run_scenario_builder(
                experiment_spec, request, steps
            )
            steps.append(scenario_step)

            if scenario_step.status == "failed":
                return self._create_result(
                    execution_id, request.request_id, experiment_id, "failed", steps,
                    None, started_at, start_time, scenario_step.error_message
                )

            # 3. Network Builder (Baseline + Alternatives)
            network_artifacts = {}
            for net_req in scenario_plan["network_build_requests"]:
                variant_id = net_req["variant_id"]
                artifact, network_step = await self._run_network_builder(
                    net_req, request, steps
                )
                steps.append(network_step)

                if network_step.status == "failed":
                    return self._create_result(
                        execution_id, request.request_id, experiment_id, "partial", steps,
                        None, started_at, start_time, network_step.error_message
                    )

                network_artifacts[variant_id] = artifact

            # 4. Demand Builder (Baseline + Alternatives)
            demand_artifacts = {}
            for dem_req in scenario_plan["demand_build_requests"]:
                variant_id = dem_req["variant_id"]
                artifact, demand_step = await self._run_demand_builder(
                    dem_req, request, steps
                )
                steps.append(demand_step)

                if demand_step.status == "failed":
                    return self._create_result(
                        execution_id, request.request_id, experiment_id, "partial", steps,
                        None, started_at, start_time, demand_step.error_message
                    )

                demand_artifacts[variant_id] = artifact

            # 5. Simulator Runner (Baseline + Alternatives)
            simulation_artifacts = {}
            for variant_id in network_artifacts.keys():
                sim_req = {
                    "schema_version": "1.0",
                    "request_id": request.request_id,
                    "experiment_id": experiment_id,
                    "variant_id": variant_id,
                    "network_artifact": network_artifacts[variant_id],
                    "demand_artifact": demand_artifacts[variant_id],
                }

                artifact, sim_step = await self._run_simulator(
                    sim_req, request, steps
                )
                steps.append(sim_step)

                if sim_step.status == "failed":
                    return self._create_result(
                        execution_id, request.request_id, experiment_id, "partial", steps,
                        None, started_at, start_time, sim_step.error_message
                    )

                simulation_artifacts[variant_id] = artifact

            # 6. Analyzer
            baseline_sim = simulation_artifacts.get("baseline")
            alternative_sims = [
                sim for vid, sim in simulation_artifacts.items() if vid != "baseline"
            ]

            analysis_result, analyzer_step = await self._run_analyzer(
                experiment_id, request.request_id, baseline_sim, alternative_sims,
                request, steps
            )
            steps.append(analyzer_step)

            if analyzer_step.status == "failed":
                return self._create_result(
                    execution_id, request.request_id, experiment_id, "partial", steps,
                    None, started_at, start_time, analyzer_step.error_message
                )

            # 7. Reporter
            report_artifact, reporter_step = await self._run_reporter(
                experiment_id, request.request_id, request.user_request,
                analysis_result, request, steps
            )
            steps.append(reporter_step)

            if reporter_step.status == "failed":
                return self._create_result(
                    execution_id, request.request_id, experiment_id, "partial", steps,
                    None, started_at, start_time, reporter_step.error_message
                )

            # 성공
            return self._create_result(
                execution_id, request.request_id, experiment_id, "completed", steps,
                report_artifact["report_uri"], started_at, start_time, None
            )

        except Exception as e:
            # 예상치 못한 에러
            error_step = PipelineStepStatus(
                step_name="pipeline",
                status="failed",
                error_message=str(e),
            )
            steps.append(error_step)

            return self._create_result(
                execution_id, request.request_id, experiment_id, "failed", steps,
                None, started_at, start_time, str(e)
            )

    async def _run_orchestrator(
        self, request: PipelineExecutionRequest, steps: list
    ) -> tuple[dict, PipelineStepStatus]:
        """Orchestrator 실행"""
        if "orchestrator" in request.skip_steps:
            return {}, self._create_skipped_step("orchestrator")

        step_start = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.orchestrator_url}/orchestrator/parse",
                    json={"user_input": request.user_request},
                )
                response.raise_for_status()
                result = response.json()

            duration_ms = (time.time() - step_start) * 1000
            completed_at = datetime.utcnow().isoformat()

            step = PipelineStepStatus(
                step_name="orchestrator",
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

            return result["experiment_spec"], step

        except Exception as e:
            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name="orchestrator",
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                error_message=str(e),
            )
            return {}, step

    async def _run_scenario_builder(
        self, experiment_spec: dict, request: PipelineExecutionRequest, steps: list
    ) -> tuple[dict, PipelineStepStatus]:
        """Scenario Builder 실행"""
        if "scenario_builder" in request.skip_steps:
            return {}, self._create_skipped_step("scenario_builder")

        step_start = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.scenario_builder_url}/scenario-builder/build",
                    json={"experiment_spec": experiment_spec},
                )
                response.raise_for_status()
                result = response.json()

            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name="scenario_builder",
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
            )

            return result["scenario_plan"], step

        except Exception as e:
            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name="scenario_builder",
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                error_message=str(e),
            )
            return {}, step

    async def _run_network_builder(
        self, network_request: dict, request: PipelineExecutionRequest, steps: list
    ) -> tuple[dict, PipelineStepStatus]:
        """Network Builder 실행"""
        variant_id = network_request["variant_id"]

        if "network_builder" in request.skip_steps:
            return {}, self._create_skipped_step(f"network_builder_{variant_id}")

        step_start = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.network_builder_url}/network/build",
                    json={"network_build_request": network_request},
                )
                response.raise_for_status()
                artifact = response.json()

            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name=f"network_builder_{variant_id}",
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                artifact_uri=artifact.get("uri"),
            )

            return artifact, step

        except Exception as e:
            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name=f"network_builder_{variant_id}",
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                error_message=str(e),
            )
            return {}, step

    async def _run_demand_builder(
        self, demand_request: dict, request: PipelineExecutionRequest, steps: list
    ) -> tuple[dict, PipelineStepStatus]:
        """Demand Builder 실행"""
        variant_id = demand_request["variant_id"]

        if "demand_builder" in request.skip_steps:
            return {}, self._create_skipped_step(f"demand_builder_{variant_id}")

        step_start = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.demand_builder_url}/demand/build",
                    json={"demand_build_request": demand_request},
                )
                response.raise_for_status()
                artifact = response.json()

            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name=f"demand_builder_{variant_id}",
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                artifact_uri=artifact.get("uri"),
            )

            return artifact, step

        except Exception as e:
            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name=f"demand_builder_{variant_id}",
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                error_message=str(e),
            )
            return {}, step

    async def _run_simulator(
        self, sim_request: dict, request: PipelineExecutionRequest, steps: list
    ) -> tuple[dict, PipelineStepStatus]:
        """Simulator Runner 실행"""
        variant_id = sim_request["variant_id"]

        if "simulator_runner" in request.skip_steps or request.dry_run:
            # Dry Run: 더미 아티팩트 반환
            return self._create_dummy_simulation_artifact(sim_request), \
                   self._create_skipped_step(f"simulator_runner_{variant_id}")

        step_start = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.simulator_runner_url}/simulation/run",
                    json={"simulation_run_request": sim_request},
                )
                response.raise_for_status()
                artifact = response.json()

            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name=f"simulator_runner_{variant_id}",
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                artifact_uri=artifact.get("outputs", {}).get("tripinfo"),
            )

            return artifact, step

        except Exception as e:
            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name=f"simulator_runner_{variant_id}",
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                error_message=str(e),
            )
            return {}, step

    async def _run_analyzer(
        self, experiment_id: str, request_id: str, baseline_sim: dict,
        alternative_sims: list, request: PipelineExecutionRequest, steps: list
    ) -> tuple[dict, PipelineStepStatus]:
        """Analyzer 실행"""
        if "analyzer" in request.skip_steps:
            return {}, self._create_skipped_step("analyzer")

        step_start = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            analysis_request = {
                "schema_version": "1.0",
                "request_id": request_id,
                "experiment_id": experiment_id,
                "baseline_simulation": baseline_sim,
                "alternative_simulations": alternative_sims,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.analyzer_url}/analysis/run",
                    json={"analysis_request": analysis_request},
                )
                response.raise_for_status()
                result = response.json()

            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name="analyzer",
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
            )

            return result, step

        except Exception as e:
            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name="analyzer",
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                error_message=str(e),
            )
            return {}, step

    async def _run_reporter(
        self, experiment_id: str, request_id: str, user_request: str,
        analysis_result: dict, request: PipelineExecutionRequest, steps: list
    ) -> tuple[dict, PipelineStepStatus]:
        """Reporter 실행"""
        if "reporter" in request.skip_steps:
            return {}, self._create_skipped_step("reporter")

        step_start = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            report_request = {
                "schema_version": "1.0",
                "request_id": request_id,
                "experiment_id": experiment_id,
                "analysis_result": analysis_result,
                "user_request": user_request,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.reporter_url}/report/generate",
                    json={
                        "report_request": report_request,
                        "reporter_type": "template",  # 초기에는 template 사용
                    },
                )
                response.raise_for_status()
                artifact = response.json()

            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name="reporter",
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                artifact_uri=artifact.get("report_uri"),
            )

            return artifact, step

        except Exception as e:
            duration_ms = (time.time() - step_start) * 1000
            step = PipelineStepStatus(
                step_name="reporter",
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=duration_ms,
                error_message=str(e),
            )
            return {}, step

    def _create_skipped_step(self, step_name: str) -> PipelineStepStatus:
        """건너뛴 단계 생성"""
        return PipelineStepStatus(
            step_name=step_name,
            status="skipped",
        )

    def _create_dummy_simulation_artifact(self, sim_request: dict) -> dict:
        """더미 시뮬레이션 아티팩트 (Dry Run용)"""
        return {
            "schema_version": "1.0",
            "artifact_id": f"sim-dummy-{sim_request['variant_id']}",
            "request_id": sim_request["request_id"],
            "experiment_id": sim_request["experiment_id"],
            "variant_id": sim_request["variant_id"],
            "outputs": {
                "tripinfo": "dry-run://dummy/tripinfo.xml",
                "summary": "dry-run://dummy/summary.xml",
            },
            "statistics": {},
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
        }

    def _create_result(
        self,
        execution_id: str,
        request_id: str,
        experiment_id: Optional[str],
        status: str,
        steps: list,
        report_uri: Optional[str],
        started_at: str,
        start_time: float,
        error_message: Optional[str],
    ) -> PipelineExecutionResult:
        """파이프라인 결과 생성"""
        total_duration_ms = (time.time() - start_time) * 1000
        completed_at = datetime.utcnow().isoformat()

        return PipelineExecutionResult(
            execution_id=execution_id,
            request_id=request_id,
            experiment_id=experiment_id or "unknown",
            status=status,
            steps=steps,
            report_uri=report_uri,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            error_message=error_message,
        )
