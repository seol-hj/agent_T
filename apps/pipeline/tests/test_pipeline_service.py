"""
Pipeline Service 단위 테스트
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas.pipeline import PipelineExecutionRequest, PipelineExecutionResult
from common.schemas.experiment import ExperimentSpec
from common.schemas.scenario import ScenarioPlan, NetworkBuildRequest, DemandBuildRequest
from common.schemas.network import NetworkArtifact
from common.schemas.demand import DemandArtifact
from common.schemas.simulation import SimulationRunArtifact
from common.schemas.analysis import AnalysisResult, ScenarioComparison, KPIData, ImprovementSummary
from common.schemas.report import ReportArtifact

from apps.pipeline.services.pipeline_service import PipelineService


@pytest.fixture
def pipeline_service():
    """PipelineService 인스턴스"""
    return PipelineService(
        orchestrator_url="http://orchestrator:8001",
        scenario_builder_url="http://scenario-builder:8002",
        network_builder_url="http://network-builder:8003",
        demand_builder_url="http://demand-builder:8004",
        simulator_runner_url="http://simulator-runner:8005",
        analyzer_url="http://analyzer:8006",
        reporter_url="http://reporter:8007",
    )


@pytest.fixture
def sample_experiment_spec():
    """샘플 ExperimentSpec"""
    return ExperimentSpec(
        version="1.0.0",
        experiment_id="exp_001",
        user_request="강남역 일대 교통량 20% 증가 시뮬레이션",
        area={
            "center": {"lat": 37.4979, "lon": 127.0276},
            "radius_m": 1000
        },
        baseline_conditions={
            "time_range": {"start": "08:00", "end": "09:00"},
            "demand_level": "peak_hour"
        },
        scenarios=[
            {
                "scenario_id": "alt_demand_increase",
                "type": "demand_increase",
                "parameters": {"multiplier": 1.2}
            }
        ],
        metrics_of_interest=["travel_time", "queue_length"],
        simulation_duration_seconds=3600,
        clarification_questions=[],
        confidence_score=0.85
    )


@pytest.fixture
def sample_scenario_plan():
    """샘플 ScenarioPlan"""
    return ScenarioPlan(
        version="1.0.0",
        plan_id="plan_001",
        experiment_id="exp_001",
        baseline=NetworkBuildRequest(
            request_id="req_baseline",
            experiment_id="exp_001",
            area={"center": {"lat": 37.4979, "lon": 127.0276}, "radius_m": 1000},
            network_source="toy",
            modifications=[],
            output_format="sumo_net"
        ),
        alternatives=[
            NetworkBuildRequest(
                request_id="req_alt_demand_increase",
                experiment_id="exp_001",
                area={"center": {"lat": 37.4979, "lon": 127.0276}, "radius_m": 1000},
                network_source="toy",
                modifications=[],
                output_format="sumo_net"
            )
        ],
        demand_baseline=DemandBuildRequest(
            request_id="req_demand_baseline",
            experiment_id="exp_001",
            network_artifact_uri="s3://bucket/network_baseline.net.xml",
            time_range={"start": "08:00", "end": "09:00"},
            demand_level="peak_hour",
            demand_source="toy",
            vehicle_types={"car": 0.9, "bus": 0.1},
            output_format="sumo_routes"
        ),
        demand_alternatives=[
            DemandBuildRequest(
                request_id="req_demand_alt",
                experiment_id="exp_001",
                network_artifact_uri="s3://bucket/network_alt.net.xml",
                time_range={"start": "08:00", "end": "09:00"},
                demand_level="peak_hour",
                demand_source="toy",
                demand_multiplier=1.2,
                vehicle_types={"car": 0.9, "bus": 0.1},
                output_format="sumo_routes"
            )
        ],
        summary="베이스라인 + 교통량 20% 증가 시나리오"
    )


@pytest.fixture
def sample_network_artifact():
    """샘플 NetworkArtifact"""
    return NetworkArtifact(
        version="1.0.0",
        artifact_id="net_001",
        request_id="req_baseline",
        experiment_id="exp_001",
        network_file_uri="s3://bucket/network_baseline.net.xml",
        metadata={
            "node_count": 16,
            "edge_count": 24,
            "source": "toy"
        },
        created_at=datetime.utcnow().isoformat()
    )


@pytest.fixture
def sample_demand_artifact():
    """샘플 DemandArtifact"""
    return DemandArtifact(
        version="1.0.0",
        artifact_id="demand_001",
        request_id="req_demand_baseline",
        experiment_id="exp_001",
        routes_file_uri="s3://bucket/demand_baseline.rou.xml",
        metadata={
            "vehicle_count": 100,
            "vehicle_types": {"car": 90, "bus": 10}
        },
        created_at=datetime.utcnow().isoformat()
    )


@pytest.fixture
def sample_simulation_artifact():
    """샘플 SimulationRunArtifact"""
    return SimulationRunArtifact(
        version="1.0.0",
        artifact_id="sim_001",
        request_id="req_sim_baseline",
        experiment_id="exp_001",
        variant_id="baseline",
        config_file_uri="s3://bucket/baseline.sumocfg",
        output_tripinfo_uri="s3://bucket/baseline_tripinfo.xml",
        output_summary_uri="s3://bucket/baseline_summary.xml",
        output_queue_uri="s3://bucket/baseline_queue.xml",
        output_emission_uri="s3://bucket/baseline_emission.xml",
        execution_status="completed",
        execution_time_ms=5000,
        metadata={"sumo_version": "1.18.0"},
        created_at=datetime.utcnow().isoformat()
    )


@pytest.fixture
def sample_analysis_result():
    """샘플 AnalysisResult"""
    return AnalysisResult(
        version="1.0.0",
        result_id="analysis_001",
        experiment_id="exp_001",
        baseline_kpis=KPIData(
            variant_id="baseline",
            avg_travel_time=300.0,
            avg_waiting_time=60.0,
            avg_speed=8.5,
            total_vehicles=100,
            completed_trips=95,
            avg_queue_length=5.0,
            max_queue_length=12.0,
            total_co2=1500.0,
            total_nox=50.0,
            total_pmx=5.0
        ),
        alternative_kpis=[
            KPIData(
                variant_id="alt_demand_increase",
                avg_travel_time=360.0,
                avg_waiting_time=80.0,
                avg_speed=7.5,
                total_vehicles=120,
                completed_trips=110,
                avg_queue_length=7.0,
                max_queue_length=15.0,
                total_co2=1800.0,
                total_nox=60.0,
                total_pmx=6.0
            )
        ],
        comparisons=[
            ScenarioComparison(
                variant_id="alt_demand_increase",
                improvement_summary=ImprovementSummary(
                    improved_count=0,
                    worsened_count=10,
                    neutral_count=0,
                    overall_score=-25.5
                ),
                improvements={
                    "avg_travel_time": {"baseline": 300.0, "alternative": 360.0, "improvement_rate": -20.0},
                    "avg_waiting_time": {"baseline": 60.0, "alternative": 80.0, "improvement_rate": -33.3}
                },
                summary="교통량 증가로 모든 지표 악화"
            )
        ],
        created_at=datetime.utcnow().isoformat()
    )


@pytest.fixture
def sample_report_artifact():
    """샘플 ReportArtifact"""
    return ReportArtifact(
        version="1.0.0",
        artifact_id="report_001",
        experiment_id="exp_001",
        report_markdown_uri="s3://bucket/report_001.md",
        report_pdf_uri=None,
        summary="교통량 증가 시 모든 지표 악화",
        key_findings=[
            "평균 통행시간 20% 증가",
            "평균 대기시간 33% 증가"
        ],
        created_at=datetime.utcnow().isoformat()
    )


@pytest.mark.asyncio
async def test_execute_pipeline_success(
    pipeline_service,
    sample_experiment_spec,
    sample_scenario_plan,
    sample_network_artifact,
    sample_demand_artifact,
    sample_simulation_artifact,
    sample_analysis_result,
    sample_report_artifact
):
    """정상 파이프라인 실행 테스트"""

    # Mock httpx.AsyncClient
    with patch("httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock responses
        mock_client.post = AsyncMock(side_effect=[
            # Orchestrator
            MagicMock(status_code=200, json=lambda: sample_experiment_spec.model_dump()),
            # Scenario Builder
            MagicMock(status_code=200, json=lambda: sample_scenario_plan.model_dump()),
            # Network Builder (baseline)
            MagicMock(status_code=200, json=lambda: sample_network_artifact.model_dump()),
            # Network Builder (alternative)
            MagicMock(status_code=200, json=lambda: sample_network_artifact.model_dump()),
            # Demand Builder (baseline)
            MagicMock(status_code=200, json=lambda: sample_demand_artifact.model_dump()),
            # Demand Builder (alternative)
            MagicMock(status_code=200, json=lambda: sample_demand_artifact.model_dump()),
            # Simulator Runner (baseline)
            MagicMock(status_code=200, json=lambda: sample_simulation_artifact.model_dump()),
            # Simulator Runner (alternative)
            MagicMock(status_code=200, json=lambda: sample_simulation_artifact.model_dump()),
            # Analyzer
            MagicMock(status_code=200, json=lambda: sample_analysis_result.model_dump()),
            # Reporter
            MagicMock(status_code=200, json=lambda: sample_report_artifact.model_dump()),
        ])

        # Execute
        request = PipelineExecutionRequest(
            user_request="강남역 일대 교통량 20% 증가 시뮬레이션",
            experiment_id="exp_001",
            dry_run=False,
            skip_steps=[]
        )

        result = await pipeline_service.execute_pipeline(request)

        # Assertions
        assert result.status == "completed"
        assert result.experiment_id == "exp_001"
        assert result.report_uri == sample_report_artifact.report_markdown_uri
        assert result.error_message is None

        # All steps completed
        assert len(result.steps) == 7
        for step in result.steps:
            assert step.status == "completed"
            assert step.duration_ms is not None
            assert step.duration_ms > 0


@pytest.mark.asyncio
async def test_execute_pipeline_dry_run(pipeline_service):
    """Dry Run 모드 테스트"""

    with patch("httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock responses (더미 데이터)
        mock_client.post = AsyncMock(side_effect=[
            # Orchestrator
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "experiment_id": "exp_dry",
                "user_request": "테스트",
                "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                "baseline_conditions": {"time_range": {"start": "08:00", "end": "09:00"}},
                "scenarios": [],
                "metrics_of_interest": ["travel_time"],
                "simulation_duration_seconds": 3600,
                "clarification_questions": [],
                "confidence_score": 0.9
            }),
            # Scenario Builder
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "plan_id": "plan_dry",
                "experiment_id": "exp_dry",
                "baseline": {
                    "request_id": "req_baseline",
                    "experiment_id": "exp_dry",
                    "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                    "network_source": "toy",
                    "modifications": [],
                    "output_format": "sumo_net"
                },
                "alternatives": [],
                "demand_baseline": {
                    "request_id": "req_demand_baseline",
                    "experiment_id": "exp_dry",
                    "network_artifact_uri": "s3://bucket/network.net.xml",
                    "time_range": {"start": "08:00", "end": "09:00"},
                    "demand_source": "toy",
                    "output_format": "sumo_routes"
                },
                "demand_alternatives": [],
                "summary": "Dry run"
            }),
            # Network Builder (baseline)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "net_dry",
                "request_id": "req_baseline",
                "experiment_id": "exp_dry",
                "network_file_uri": "s3://bucket/network.net.xml",
                "metadata": {},
                "created_at": datetime.utcnow().isoformat()
            }),
            # Demand Builder (baseline)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "demand_dry",
                "request_id": "req_demand_baseline",
                "experiment_id": "exp_dry",
                "routes_file_uri": "s3://bucket/demand.rou.xml",
                "metadata": {},
                "created_at": datetime.utcnow().isoformat()
            }),
            # Simulator Runner (baseline, dry_run=true)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "sim_dry",
                "request_id": "req_sim_baseline",
                "experiment_id": "exp_dry",
                "variant_id": "baseline",
                "config_file_uri": "s3://bucket/baseline.sumocfg",
                "output_tripinfo_uri": "s3://bucket/baseline_tripinfo.xml",
                "output_summary_uri": "s3://bucket/baseline_summary.xml",
                "output_queue_uri": "s3://bucket/baseline_queue.xml",
                "output_emission_uri": "s3://bucket/baseline_emission.xml",
                "execution_status": "completed",
                "execution_time_ms": 100,
                "metadata": {"dry_run": True},
                "created_at": datetime.utcnow().isoformat()
            }),
            # Analyzer
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "result_id": "analysis_dry",
                "experiment_id": "exp_dry",
                "baseline_kpis": {
                    "variant_id": "baseline",
                    "avg_travel_time": 300.0,
                    "total_vehicles": 100
                },
                "alternative_kpis": [],
                "comparisons": [],
                "created_at": datetime.utcnow().isoformat()
            }),
            # Reporter
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "report_dry",
                "experiment_id": "exp_dry",
                "report_markdown_uri": "s3://bucket/report_dry.md",
                "summary": "Dry run",
                "key_findings": [],
                "created_at": datetime.utcnow().isoformat()
            }),
        ])

        # Execute
        request = PipelineExecutionRequest(
            user_request="테스트",
            experiment_id="exp_dry",
            dry_run=True,
            skip_steps=[]
        )

        result = await pipeline_service.execute_pipeline(request)

        # Assertions
        assert result.status == "completed"
        assert result.experiment_id == "exp_dry"


@pytest.mark.asyncio
async def test_execute_pipeline_with_skip_steps(pipeline_service):
    """skip_steps 옵션 테스트"""

    with patch("httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock responses (Orchestrator와 Scenario Builder만)
        mock_client.post = AsyncMock(side_effect=[
            # Orchestrator
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "experiment_id": "exp_skip",
                "user_request": "테스트",
                "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                "baseline_conditions": {"time_range": {"start": "08:00", "end": "09:00"}},
                "scenarios": [],
                "metrics_of_interest": ["travel_time"],
                "simulation_duration_seconds": 3600,
                "clarification_questions": [],
                "confidence_score": 0.9
            }),
            # Scenario Builder
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "plan_id": "plan_skip",
                "experiment_id": "exp_skip",
                "baseline": {
                    "request_id": "req_baseline",
                    "experiment_id": "exp_skip",
                    "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                    "network_source": "toy",
                    "modifications": [],
                    "output_format": "sumo_net"
                },
                "alternatives": [],
                "demand_baseline": {
                    "request_id": "req_demand_baseline",
                    "experiment_id": "exp_skip",
                    "network_artifact_uri": "s3://bucket/network.net.xml",
                    "time_range": {"start": "08:00", "end": "09:00"},
                    "demand_source": "toy",
                    "output_format": "sumo_routes"
                },
                "demand_alternatives": [],
                "summary": "Skip test"
            }),
        ])

        # Execute (나머지 단계 스킵)
        request = PipelineExecutionRequest(
            user_request="테스트",
            experiment_id="exp_skip",
            dry_run=False,
            skip_steps=["network_builder", "demand_builder", "simulator_runner", "analyzer", "reporter"]
        )

        result = await pipeline_service.execute_pipeline(request)

        # Assertions
        assert result.status == "completed"
        assert result.experiment_id == "exp_skip"

        # Orchestrator와 Scenario Builder만 completed, 나머지는 skipped
        assert result.steps[0].status == "completed"  # orchestrator
        assert result.steps[1].status == "completed"  # scenario_builder
        assert result.steps[2].status == "skipped"    # network_builder
        assert result.steps[3].status == "skipped"    # demand_builder
        assert result.steps[4].status == "skipped"    # simulator_runner
        assert result.steps[5].status == "skipped"    # analyzer
        assert result.steps[6].status == "skipped"    # reporter


@pytest.mark.asyncio
async def test_execute_pipeline_failure_in_orchestrator(pipeline_service):
    """Orchestrator 단계 실패 테스트"""

    with patch("httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock response (Orchestrator 실패)
        mock_client.post = AsyncMock(side_effect=[
            MagicMock(status_code=500, json=lambda: {"detail": "LLM Gateway error"})
        ])

        # Execute
        request = PipelineExecutionRequest(
            user_request="테스트",
            experiment_id="exp_fail",
            dry_run=False,
            skip_steps=[]
        )

        result = await pipeline_service.execute_pipeline(request)

        # Assertions
        assert result.status == "failed"
        assert result.experiment_id == "exp_fail"
        assert result.error_message is not None
        assert "orchestrator" in result.error_message.lower()

        # Orchestrator는 failed, 나머지는 pending
        assert result.steps[0].status == "failed"
        assert result.steps[0].error_message is not None
        for i in range(1, 7):
            assert result.steps[i].status == "pending"


@pytest.mark.asyncio
async def test_execute_pipeline_failure_in_network_builder(pipeline_service):
    """Network Builder 단계 실패 테스트"""

    with patch("httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock responses
        mock_client.post = AsyncMock(side_effect=[
            # Orchestrator (성공)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "experiment_id": "exp_fail_net",
                "user_request": "테스트",
                "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                "baseline_conditions": {"time_range": {"start": "08:00", "end": "09:00"}},
                "scenarios": [],
                "metrics_of_interest": ["travel_time"],
                "simulation_duration_seconds": 3600,
                "clarification_questions": [],
                "confidence_score": 0.9
            }),
            # Scenario Builder (성공)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "plan_id": "plan_fail_net",
                "experiment_id": "exp_fail_net",
                "baseline": {
                    "request_id": "req_baseline",
                    "experiment_id": "exp_fail_net",
                    "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                    "network_source": "toy",
                    "modifications": [],
                    "output_format": "sumo_net"
                },
                "alternatives": [],
                "demand_baseline": {
                    "request_id": "req_demand_baseline",
                    "experiment_id": "exp_fail_net",
                    "network_artifact_uri": "s3://bucket/network.net.xml",
                    "time_range": {"start": "08:00", "end": "09:00"},
                    "demand_source": "toy",
                    "output_format": "sumo_routes"
                },
                "demand_alternatives": [],
                "summary": "Fail test"
            }),
            # Network Builder (실패)
            MagicMock(status_code=500, json=lambda: {"detail": "Network generation failed"})
        ])

        # Execute
        request = PipelineExecutionRequest(
            user_request="테스트",
            experiment_id="exp_fail_net",
            dry_run=False,
            skip_steps=[]
        )

        result = await pipeline_service.execute_pipeline(request)

        # Assertions
        assert result.status == "failed"
        assert result.experiment_id == "exp_fail_net"
        assert result.error_message is not None
        assert "network_builder" in result.error_message.lower()

        # Orchestrator와 Scenario Builder는 completed, Network Builder는 failed, 나머지는 pending
        assert result.steps[0].status == "completed"  # orchestrator
        assert result.steps[1].status == "completed"  # scenario_builder
        assert result.steps[2].status == "failed"     # network_builder
        for i in range(3, 7):
            assert result.steps[i].status == "pending"
