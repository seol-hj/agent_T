"""
Schema Validation Tests

모든 Pydantic Schema에 대한 검증 테스트
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from common.schemas import (
    UserRequest,
    ExperimentSpec,
    ScenarioPlan,
    ScenarioVariant,
    NetworkBuildRequest,
    NetworkArtifact,
    DemandBuildRequest,
    DemandArtifact,
    SimulationRunRequest,
    SimulationRunArtifact,
    AnalysisResult,
    KPIComparison,
    BaselineKPI,
    AlternativeKPI,
    ReportArtifact,
    ReportSection,
    AgentLog,
    LogLevel,
    ModelVersion,
    PromptVersion,
)


# UserRequest Tests
class TestUserRequest:
    def test_user_request_valid(self):
        data = {
            "request_id": "req-001",
            "user_id": "user-001",
            "raw_input": "서울 강남구 출퇴근 시간대 교통량 분석",
            "language": "ko",
        }
        request = UserRequest(**data)
        assert request.request_id == "req-001"
        assert request.schema_version == "1.0"
        assert request.language == "ko"

    def test_user_request_missing_required(self):
        with pytest.raises(ValidationError):
            UserRequest(request_id="req-001")


# ExperimentSpec Tests
class TestExperimentSpec:
    def test_experiment_spec_valid(self):
        data = {
            "experiment_id": "exp-001",
            "request_id": "req-001",
            "title": "강남구 신호등 최적화",
            "description": "출퇴근 시간대 교통 혼잡 완화",
            "location": {"region": "강남구", "bbox": [127.0, 37.4, 127.1, 37.5]},
            "time_settings": {"start_time": "07:00", "end_time": "09:00"},
            "traffic_settings": {"vehicle_count": 5000},
            "objectives": ["통행 시간 단축"],
        }
        spec = ExperimentSpec(**data)
        assert spec.experiment_id == "exp-001"
        assert spec.schema_version == "1.0"
        assert len(spec.objectives) == 1


# ScenarioPlan Tests
class TestScenarioPlan:
    def test_scenario_plan_valid(self):
        baseline = {
            "variant_id": "base-001",
            "variant_type": "baseline",
            "name": "현재 신호 체계",
            "description": "현재 상태",
            "parameters": {"signal_cycle": 120},
        }
        alternative = {
            "variant_id": "alt-001",
            "variant_type": "alternative",
            "name": "최적화된 신호",
            "description": "개선안",
            "parameters": {"signal_cycle": 90},
        }
        data = {
            "plan_id": "plan-001",
            "experiment_id": "exp-001",
            "baseline": baseline,
            "alternatives": [alternative],
            "comparison_objectives": ["통행 시간 단축"],
        }
        plan = ScenarioPlan(**data)
        assert plan.baseline.variant_type == "baseline"
        assert len(plan.alternatives) == 1
        assert plan.alternatives[0].variant_type == "alternative"

    def test_scenario_plan_no_alternatives_fails(self):
        baseline = {
            "variant_id": "base-001",
            "variant_type": "baseline",
            "name": "현재",
            "description": "현재 상태",
            "parameters": {},
        }
        with pytest.raises(ValidationError):
            ScenarioPlan(
                plan_id="plan-001",
                experiment_id="exp-001",
                baseline=baseline,
                alternatives=[],
                comparison_objectives=["목표"],
            )


# NetworkBuildRequest Tests
class TestNetworkBuildRequest:
    def test_network_build_request_valid(self):
        data = {
            "request_id": "netreq-001",
            "experiment_id": "exp-001",
            "variant_id": "base-001",
            "osm_source": {
                "type": "bbox",
                "bbox": [127.0, 37.4, 127.1, 37.5],
            },
        }
        request = NetworkBuildRequest(**data)
        assert request.schema_version == "1.0"
        assert request.variant_id == "base-001"


# NetworkArtifact Tests
class TestNetworkArtifact:
    def test_network_artifact_valid(self):
        data = {
            "artifact_id": "net-001",
            "request_id": "netreq-001",
            "experiment_id": "exp-001",
            "variant_id": "base-001",
            "uri": "s3://bucket/network.net.xml",
            "file_size_bytes": 1024576,
            "statistics": {"nodes": 1234, "edges": 2345},
        }
        artifact = NetworkArtifact(**data)
        assert artifact.file_format == "net.xml"
        assert artifact.file_size_bytes == 1024576


# DemandBuildRequest Tests
class TestDemandBuildRequest:
    def test_demand_build_request_valid(self):
        data = {
            "request_id": "demreq-001",
            "experiment_id": "exp-001",
            "variant_id": "base-001",
            "network_artifact_id": "net-001",
            "demand_settings": {"vehicle_count": 5000},
        }
        request = DemandBuildRequest(**data)
        assert request.network_artifact_id == "net-001"


# DemandArtifact Tests
class TestDemandArtifact:
    def test_demand_artifact_valid(self):
        data = {
            "artifact_id": "dem-001",
            "request_id": "demreq-001",
            "experiment_id": "exp-001",
            "variant_id": "base-001",
            "uri": "s3://bucket/routes.rou.xml",
            "file_size_bytes": 2048000,
            "statistics": {"total_vehicles": 5000},
        }
        artifact = DemandArtifact(**data)
        assert artifact.file_format == "rou.xml"


# SimulationRunRequest Tests
class TestSimulationRunRequest:
    def test_simulation_run_request_valid(self):
        data = {
            "request_id": "simreq-001",
            "experiment_id": "exp-001",
            "variant_id": "base-001",
            "network_artifact_id": "net-001",
            "demand_artifact_id": "dem-001",
            "simulation_settings": {"step_length": 1.0, "begin": 0, "end": 7200},
        }
        request = SimulationRunRequest(**data)
        assert request.network_artifact_id == "net-001"
        assert request.demand_artifact_id == "dem-001"


# SimulationRunArtifact Tests
class TestSimulationRunArtifact:
    def test_simulation_run_artifact_valid(self):
        data = {
            "artifact_id": "sim-001",
            "request_id": "simreq-001",
            "experiment_id": "exp-001",
            "variant_id": "base-001",
            "uri": "s3://bucket/sim/",
            "output_files": {"tripinfo": "s3://bucket/tripinfo.xml"},
            "status": "completed",
            "statistics": {"total_vehicles": 5000},
        }
        artifact = SimulationRunArtifact(**data)
        assert artifact.status == "completed"

    def test_simulation_run_artifact_invalid_status(self):
        data = {
            "artifact_id": "sim-001",
            "request_id": "simreq-001",
            "experiment_id": "exp-001",
            "variant_id": "base-001",
            "uri": "s3://bucket/sim/",
            "output_files": {},
            "status": "invalid_status",
            "statistics": {},
        }
        with pytest.raises(ValidationError):
            SimulationRunArtifact(**data)


# AnalysisResult Tests
class TestAnalysisResult:
    def test_analysis_result_valid(self):
        baseline = {
            "variant_id": "base-001",
            "avg_trip_duration_seconds": 1245.6,
            "avg_waiting_time_seconds": 89.3,
            "total_co2_kg": 2456.8,
            "avg_speed_kmh": 28.5,
            "completed_trips": 4987,
            "teleports": 13,
        }
        alternative = {
            "variant_id": "alt-001",
            "avg_trip_duration_seconds": 1045.2,
            "avg_waiting_time_seconds": 62.7,
            "total_co2_kg": 2089.4,
            "avg_speed_kmh": 34.2,
            "completed_trips": 4995,
            "teleports": 5,
            "improvements": {
                "trip_duration": -16.1,
                "waiting_time": -29.8,
                "co2_emission": -15.0,
                "speed": 20.0,
            },
        }
        kpi_comparison = {
            "baseline": baseline,
            "alternatives": [alternative],
            "best_alternative_id": "alt-001",
            "recommendation_summary": "통행 시간 16.1% 단축",
        }
        data = {
            "analysis_id": "ana-001",
            "experiment_id": "exp-001",
            "simulation_artifact_ids": ["sim-001", "sim-002"],
            "kpi_comparison": kpi_comparison,
        }
        result = AnalysisResult(**data)
        assert result.kpi_comparison.baseline.variant_id == "base-001"
        assert len(result.kpi_comparison.alternatives) == 1
        assert result.kpi_comparison.alternatives[0].improvements["trip_duration"] == -16.1


# ReportArtifact Tests
class TestReportArtifact:
    def test_report_artifact_valid(self):
        section = {
            "section_id": "summary",
            "title": "요약",
            "content": "## 주요 발견\n\n내용",
            "order": 1,
        }
        data = {
            "artifact_id": "rep-001",
            "experiment_id": "exp-001",
            "analysis_id": "ana-001",
            "title": "교통 분석 보고서",
            "uri": "s3://bucket/report.pdf",
            "file_format": "pdf",
            "sections": [section],
            "executive_summary": "통행 시간 16.1% 단축",
            "recommendations": ["신호 주기 단축"],
        }
        artifact = ReportArtifact(**data)
        assert artifact.file_format == "pdf"
        assert len(artifact.sections) == 1


# AgentLog Tests
class TestAgentLog:
    def test_agent_log_valid(self):
        data = {
            "log_id": "log-001",
            "level": "info",
            "agent_name": "scenario-builder",
            "message": "시나리오 생성 완료",
        }
        log = AgentLog(**data)
        assert log.level == LogLevel.INFO
        assert log.agent_name == "scenario-builder"

    def test_agent_log_invalid_level(self):
        with pytest.raises(ValidationError):
            AgentLog(
                log_id="log-001",
                level="invalid_level",
                agent_name="test",
                message="test",
            )


# ModelVersion Tests
class TestModelVersion:
    def test_model_version_valid(self):
        data = {
            "model_id": "anthropic.claude-3-sonnet",
            "model_name": "Claude 3 Sonnet",
            "provider": "bedrock",
            "version": "20240229",
            "capabilities": ["text-generation"],
            "context_window": 200000,
            "max_output_tokens": 4096,
        }
        version = ModelVersion(**data)
        assert version.model_id == "anthropic.claude-3-sonnet"
        assert version.context_window == 200000


# PromptVersion Tests
class TestPromptVersion:
    def test_prompt_version_valid(self):
        data = {
            "prompt_id": "scenario-gen-v2.0",
            "prompt_name": "시나리오 생성",
            "version": "v2.0",
            "agent_name": "scenario-builder",
            "template": "당신은...",
            "template_variables": ["user_input"],
            "expected_output_format": "json",
            "compatible_models": ["anthropic.claude-3-sonnet"],
        }
        version = PromptVersion(**data)
        assert version.prompt_id == "scenario-gen-v2.0"
        assert version.active is True


# Integration Tests
class TestSchemaIntegration:
    def test_full_workflow_schemas(self):
        """전체 워크플로우에서 스키마 연계 테스트"""
        # 1. UserRequest
        user_req = UserRequest(
            request_id="req-001",
            user_id="user-001",
            raw_input="강남구 교통 분석",
        )

        # 2. ExperimentSpec
        exp_spec = ExperimentSpec(
            experiment_id="exp-001",
            request_id=user_req.request_id,
            title="교통 분석",
            description="설명",
            location={"region": "강남구"},
            time_settings={"start": "07:00"},
            traffic_settings={"count": 5000},
            objectives=["목표"],
        )

        # 3. NetworkBuildRequest
        net_req = NetworkBuildRequest(
            request_id="netreq-001",
            experiment_id=exp_spec.experiment_id,
            variant_id="base-001",
            osm_source={"type": "bbox"},
        )

        # 4. NetworkArtifact
        net_art = NetworkArtifact(
            artifact_id="net-001",
            request_id=net_req.request_id,
            experiment_id=exp_spec.experiment_id,
            variant_id="base-001",
            uri="s3://network.xml",
            file_size_bytes=1024,
            statistics={"nodes": 100},
        )

        # ID 연계 확인
        assert exp_spec.request_id == user_req.request_id
        assert net_req.experiment_id == exp_spec.experiment_id
        assert net_art.experiment_id == exp_spec.experiment_id

    def test_baseline_alternative_comparison(self):
        """Baseline과 Alternative KPI 비교 테스트"""
        baseline = BaselineKPI(
            variant_id="base-001",
            avg_trip_duration_seconds=1245.6,
            avg_waiting_time_seconds=89.3,
            total_co2_kg=2456.8,
            avg_speed_kmh=28.5,
            completed_trips=4987,
            teleports=13,
        )

        alternative = AlternativeKPI(
            variant_id="alt-001",
            avg_trip_duration_seconds=1045.2,
            avg_waiting_time_seconds=62.7,
            total_co2_kg=2089.4,
            avg_speed_kmh=34.2,
            completed_trips=4995,
            teleports=5,
            improvements={
                "trip_duration": -16.1,
                "waiting_time": -29.8,
            },
        )

        comparison = KPIComparison(
            baseline=baseline,
            alternatives=[alternative],
            best_alternative_id="alt-001",
            recommendation_summary="개선됨",
        )

        assert comparison.baseline.variant_id == "base-001"
        assert comparison.alternatives[0].variant_id == "alt-001"
        assert comparison.alternatives[0].improvements["trip_duration"] == -16.1
