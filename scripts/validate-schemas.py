#!/usr/bin/env python3
"""
간단한 스키마 검증 스크립트

pytest 없이 기본 Python으로 모든 스키마 검증
"""

import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs'))

from datetime import datetime

try:
    from common.schemas import (
        UserRequest,
        ExperimentSpec,
        ScenarioPlan,
        ScenarioVariant,
        ScenarioType,
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
    print("✓ 모든 스키마 import 성공")
except Exception as e:
    print(f"✗ Import 실패: {e}")
    sys.exit(1)


def test_user_request():
    """UserRequest 검증"""
    try:
        request = UserRequest(
            request_id="req-001",
            user_id="user-001",
            raw_input="서울 강남구 출퇴근 시간대 교통량 분석",
        )
        assert request.schema_version == "1.0"
        assert request.language == "ko"
        print("✓ UserRequest 검증 성공")
        return True
    except Exception as e:
        print(f"✗ UserRequest 실패: {e}")
        return False


def test_experiment_spec():
    """ExperimentSpec 검증"""
    try:
        spec = ExperimentSpec(
            experiment_id="exp-001",
            request_id="req-001",
            title="강남구 신호등 최적화",
            description="출퇴근 시간대 교통 혼잡 완화",
            location={"region": "강남구", "bbox": [127.0, 37.4, 127.1, 37.5]},
            time_settings={"start_time": "07:00", "end_time": "09:00"},
            traffic_settings={"vehicle_count": 5000},
            objectives=["통행 시간 단축"],
        )
        assert spec.schema_version == "1.0"
        print("✓ ExperimentSpec 검증 성공")
        return True
    except Exception as e:
        print(f"✗ ExperimentSpec 실패: {e}")
        return False


def test_scenario_plan():
    """ScenarioPlan 검증"""
    try:
        baseline = ScenarioVariant(
            variant_id="base-001",
            variant_type=ScenarioType.BASELINE,
            name="현재 신호 체계",
            description="현재 상태",
            parameters={"signal_cycle": 120},
        )
        alternative = ScenarioVariant(
            variant_id="alt-001",
            variant_type=ScenarioType.ALTERNATIVE,
            name="최적화된 신호",
            description="개선안",
            parameters={"signal_cycle": 90},
        )
        plan = ScenarioPlan(
            plan_id="plan-001",
            experiment_id="exp-001",
            baseline=baseline,
            alternatives=[alternative],
            comparison_objectives=["통행 시간 단축"],
        )
        assert plan.baseline.variant_type == "baseline"
        assert len(plan.alternatives) == 1
        print("✓ ScenarioPlan 검증 성공")
        return True
    except Exception as e:
        print(f"✗ ScenarioPlan 실패: {e}")
        return False


def test_network_schemas():
    """Network 스키마 검증"""
    try:
        request = NetworkBuildRequest(
            request_id="netreq-001",
            experiment_id="exp-001",
            variant_id="base-001",
            osm_source={"type": "bbox", "bbox": [127.0, 37.4, 127.1, 37.5]},
        )
        artifact = NetworkArtifact(
            artifact_id="net-001",
            request_id="netreq-001",
            experiment_id="exp-001",
            variant_id="base-001",
            uri="s3://bucket/network.net.xml",
            file_size_bytes=1024576,
            statistics={"nodes": 1234, "edges": 2345},
        )
        assert artifact.file_format == "net.xml"
        print("✓ Network 스키마 검증 성공")
        return True
    except Exception as e:
        print(f"✗ Network 스키마 실패: {e}")
        return False


def test_demand_schemas():
    """Demand 스키마 검증"""
    try:
        request = DemandBuildRequest(
            request_id="demreq-001",
            experiment_id="exp-001",
            variant_id="base-001",
            network_artifact_id="net-001",
            demand_settings={"vehicle_count": 5000},
        )
        artifact = DemandArtifact(
            artifact_id="dem-001",
            request_id="demreq-001",
            experiment_id="exp-001",
            variant_id="base-001",
            uri="s3://bucket/routes.rou.xml",
            file_size_bytes=2048000,
            statistics={"total_vehicles": 5000},
        )
        assert artifact.file_format == "rou.xml"
        print("✓ Demand 스키마 검증 성공")
        return True
    except Exception as e:
        print(f"✗ Demand 스키마 실패: {e}")
        return False


def test_simulation_schemas():
    """Simulation 스키마 검증"""
    try:
        request = SimulationRunRequest(
            request_id="simreq-001",
            experiment_id="exp-001",
            variant_id="base-001",
            network_artifact_id="net-001",
            demand_artifact_id="dem-001",
            simulation_settings={"step_length": 1.0, "begin": 0, "end": 7200},
        )
        artifact = SimulationRunArtifact(
            artifact_id="sim-001",
            request_id="simreq-001",
            experiment_id="exp-001",
            variant_id="base-001",
            uri="s3://bucket/sim/",
            output_files={"tripinfo": "s3://bucket/tripinfo.xml"},
            status="completed",
            statistics={"total_vehicles": 5000},
        )
        assert artifact.status == "completed"
        print("✓ Simulation 스키마 검증 성공")
        return True
    except Exception as e:
        print(f"✗ Simulation 스키마 실패: {e}")
        return False


def test_analysis_schemas():
    """Analysis 스키마 검증 (Baseline/Alternative KPI 비교 포함)"""
    try:
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
                "co2_emission": -15.0,
                "speed": 20.0,
            },
        )
        comparison = KPIComparison(
            baseline=baseline,
            alternatives=[alternative],
            best_alternative_id="alt-001",
            recommendation_summary="통행 시간 16.1% 단축",
        )
        result = AnalysisResult(
            analysis_id="ana-001",
            experiment_id="exp-001",
            simulation_artifact_ids=["sim-001", "sim-002"],
            kpi_comparison=comparison,
        )
        assert result.kpi_comparison.baseline.variant_id == "base-001"
        assert result.kpi_comparison.alternatives[0].improvements["trip_duration"] == -16.1
        print("✓ Analysis 스키마 검증 성공 (Base/Alternative KPI 비교 포함)")
        return True
    except Exception as e:
        print(f"✗ Analysis 스키마 실패: {e}")
        return False


def test_report_schemas():
    """Report 스키마 검증"""
    try:
        section = ReportSection(
            section_id="summary",
            title="요약",
            content="## 주요 발견\n\n내용",
            order=1,
        )
        artifact = ReportArtifact(
            artifact_id="rep-001",
            experiment_id="exp-001",
            analysis_id="ana-001",
            title="교통 분석 보고서",
            uri="s3://bucket/report.pdf",
            file_format="pdf",
            sections=[section],
            executive_summary="통행 시간 16.1% 단축",
            recommendations=["신호 주기 단축"],
        )
        assert artifact.file_format == "pdf"
        print("✓ Report 스키마 검증 성공")
        return True
    except Exception as e:
        print(f"✗ Report 스키마 실패: {e}")
        return False


def test_logging_schemas():
    """Logging 스키마 검증"""
    try:
        log = AgentLog(
            log_id="log-001",
            level=LogLevel.INFO,
            agent_name="scenario-builder",
            message="시나리오 생성 완료",
        )
        assert log.level == "info"
        print("✓ Logging 스키마 검증 성공")
        return True
    except Exception as e:
        print(f"✗ Logging 스키마 실패: {e}")
        return False


def test_versioning_schemas():
    """Versioning 스키마 검증"""
    try:
        model = ModelVersion(
            model_id="anthropic.claude-3-sonnet",
            model_name="Claude 3 Sonnet",
            provider="bedrock",
            version="20240229",
            capabilities=["text-generation"],
            context_window=200000,
            max_output_tokens=4096,
        )
        prompt = PromptVersion(
            prompt_id="scenario-gen-v2.0",
            prompt_name="시나리오 생성",
            version="v2.0",
            agent_name="scenario-builder",
            template="당신은...",
            template_variables=["user_input"],
            expected_output_format="json",
            compatible_models=["anthropic.claude-3-sonnet"],
        )
        assert model.context_window == 200000
        assert prompt.active is True
        print("✓ Versioning 스키마 검증 성공")
        return True
    except Exception as e:
        print(f"✗ Versioning 스키마 실패: {e}")
        return False


def test_workflow_integration():
    """전체 워크플로우 통합 검증"""
    try:
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

        # ID 연계 확인
        assert exp_spec.request_id == user_req.request_id
        assert net_req.experiment_id == exp_spec.experiment_id
        print("✓ 워크플로우 통합 검증 성공")
        return True
    except Exception as e:
        print(f"✗ 워크플로우 통합 실패: {e}")
        return False


def main():
    print("=" * 60)
    print("교통 시뮬레이션 플랫폼 스키마 검증 시작")
    print("=" * 60)
    print()

    tests = [
        test_user_request,
        test_experiment_spec,
        test_scenario_plan,
        test_network_schemas,
        test_demand_schemas,
        test_simulation_schemas,
        test_analysis_schemas,
        test_report_schemas,
        test_logging_schemas,
        test_versioning_schemas,
        test_workflow_integration,
    ]

    results = []
    for test in tests:
        results.append(test())
        print()

    print("=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"검증 완료: {passed}/{total} 성공, {failed}/{total} 실패")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n모든 스키마 검증 통과! ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
