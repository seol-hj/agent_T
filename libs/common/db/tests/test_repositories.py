"""
Repository 통합 테스트
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.db.repositories import (
    ExperimentRepository,
    UserRequestRepository,
    ExperimentSpecRepository,
    ScenarioRepository,
    NetworkArtifactRepository,
    DemandArtifactRepository,
    SimulationRunRepository,
    AnalysisResultRepository,
    ReportRepository,
    AgentLogRepository,
    ModelVersionRepository,
    PromptVersionRepository,
    RAGDocumentRepository,
)


def test_experiment_repository_crud(test_session: Session):
    """Experiment Repository CRUD 테스트"""
    repo = ExperimentRepository(test_session)

    # Create
    exp = repo.create(
        id="exp_001",
        status="pending"
    )
    assert exp.id == "exp_001"
    assert exp.status == "pending"

    # Read
    exp_read = repo.get("exp_001")
    assert exp_read is not None
    assert exp_read.id == "exp_001"

    # Update
    exp_updated = repo.update("exp_001", status="running")
    assert exp_updated.status == "running"

    # Get by status
    running_exps = repo.get_by_status("running")
    assert len(running_exps) == 1
    assert running_exps[0].id == "exp_001"

    # Update status with method
    exp_completed = repo.update_status("exp_001", "completed", completed_at=datetime.utcnow())
    assert exp_completed.status == "completed"
    assert exp_completed.completed_at is not None

    # Get recent
    recent_exps = repo.get_recent(limit=10)
    assert len(recent_exps) == 1

    # Count
    count = repo.count()
    assert count == 1

    # Exists
    assert repo.exists("exp_001") is True
    assert repo.exists("exp_999") is False

    # Delete
    deleted = repo.delete("exp_001")
    assert deleted is True
    assert repo.get("exp_001") is None


def test_user_request_repository(test_session: Session):
    """UserRequest Repository 테스트"""
    repo = UserRequestRepository(test_session)

    # Create
    req1 = repo.create(
        id="req_001",
        request_text="강남역 일대 교통량 증가 시뮬레이션",
        language="ko",
        user_id="user_001"
    )
    req2 = repo.create(
        id="req_002",
        request_text="신촌역 교통 개선",
        language="ko",
        user_id="user_001"
    )

    # Get by user
    user_reqs = repo.get_by_user("user_001")
    assert len(user_reqs) == 2

    # Search by text
    search_results = repo.search_by_text("강남역", limit=10)
    assert len(search_results) == 1
    assert search_results[0].id == "req_001"


def test_experiment_spec_repository(test_session: Session):
    """ExperimentSpec Repository 테스트"""
    repo = ExperimentSpecRepository(test_session)

    # Create
    spec1 = repo.create(
        id="spec_001",
        version="1.0.0",
        spec_json={"experiment_id": "exp_001"},
        confidence_score=0.95,
        model_version_id="model_001"
    )
    spec2 = repo.create(
        id="spec_002",
        version="1.0.0",
        spec_json={"experiment_id": "exp_002"},
        confidence_score=0.75,
        model_version_id="model_001"
    )

    # Get by model version
    model_specs = repo.get_by_model_version("model_001")
    assert len(model_specs) == 2

    # Get high confidence
    high_conf_specs = repo.get_high_confidence(min_confidence=0.9, limit=10)
    assert len(high_conf_specs) == 1
    assert high_conf_specs[0].id == "spec_001"


def test_scenario_repository(test_session: Session):
    """Scenario Repository 테스트"""
    exp_repo = ExperimentRepository(test_session)
    scenario_repo = ScenarioRepository(test_session)

    # Create experiment
    exp = exp_repo.create(id="exp_001", status="pending")

    # Create scenarios
    baseline = scenario_repo.create(
        id="scenario_baseline",
        experiment_id="exp_001",
        scenario_type="baseline",
        plan_json={"baseline": True}
    )
    alt = scenario_repo.create(
        id="scenario_alt",
        experiment_id="exp_001",
        scenario_type="demand_increase",
        plan_json={"multiplier": 1.2}
    )

    # Get by experiment
    scenarios = scenario_repo.get_by_experiment("exp_001")
    assert len(scenarios) == 2

    # Get by type
    baseline_scenarios = scenario_repo.get_by_type("exp_001", "baseline")
    assert len(baseline_scenarios) == 1
    assert baseline_scenarios[0].id == "scenario_baseline"


def test_network_artifact_repository(test_session: Session):
    """NetworkArtifact Repository 테스트"""
    exp_repo = ExperimentRepository(test_session)
    scenario_repo = ScenarioRepository(test_session)
    network_repo = NetworkArtifactRepository(test_session)

    # Create experiment and scenario
    exp = exp_repo.create(id="exp_001", status="pending")
    scenario = scenario_repo.create(
        id="scenario_001",
        experiment_id="exp_001",
        scenario_type="baseline",
        plan_json={}
    )

    # Create network artifacts
    net1 = network_repo.create(
        id="net_001",
        scenario_id="scenario_001",
        request_id="req_001",
        variant_id="baseline",
        network_file_uri="s3://bucket/network_baseline.net.xml"
    )
    net2 = network_repo.create(
        id="net_002",
        scenario_id="scenario_001",
        request_id="req_002",
        variant_id="alt_1",
        network_file_uri="s3://bucket/network_alt1.net.xml"
    )

    # Get by scenario
    networks = network_repo.get_by_scenario("scenario_001")
    assert len(networks) == 2

    # Get by variant
    baseline_net = network_repo.get_by_variant("scenario_001", "baseline")
    assert baseline_net is not None
    assert baseline_net.id == "net_001"


def test_demand_artifact_repository(test_session: Session):
    """DemandArtifact Repository 테스트"""
    exp_repo = ExperimentRepository(test_session)
    scenario_repo = ScenarioRepository(test_session)
    demand_repo = DemandArtifactRepository(test_session)

    # Create experiment and scenario
    exp = exp_repo.create(id="exp_001", status="pending")
    scenario = scenario_repo.create(
        id="scenario_001",
        experiment_id="exp_001",
        scenario_type="baseline",
        plan_json={}
    )

    # Create demand artifacts
    dem1 = demand_repo.create(
        id="dem_001",
        scenario_id="scenario_001",
        request_id="req_001",
        variant_id="baseline",
        routes_file_uri="s3://bucket/demand_baseline.rou.xml"
    )

    # Get by scenario
    demands = demand_repo.get_by_scenario("scenario_001")
    assert len(demands) == 1

    # Get by variant
    baseline_dem = demand_repo.get_by_variant("scenario_001", "baseline")
    assert baseline_dem is not None
    assert baseline_dem.id == "dem_001"


def test_simulation_run_repository(test_session: Session):
    """SimulationRun Repository 테스트"""
    exp_repo = ExperimentRepository(test_session)
    sim_repo = SimulationRunRepository(test_session)

    # Create experiment
    exp = exp_repo.create(id="exp_001", status="pending")

    # Create simulation run
    sim = sim_repo.create(
        id="sim_001",
        experiment_id="exp_001",
        variant_id="baseline",
        config_file_uri="s3://bucket/config.sumocfg",
        execution_status="pending"
    )

    # Get by experiment
    sims = sim_repo.get_by_experiment("exp_001")
    assert len(sims) == 1

    # Get by variant
    baseline_sim = sim_repo.get_by_variant("exp_001", "baseline")
    assert baseline_sim is not None
    assert baseline_sim.id == "sim_001"

    # Get by status
    pending_sims = sim_repo.get_by_status("pending")
    assert len(pending_sims) == 1

    # Update status
    sim_updated = sim_repo.update_status(
        "sim_001",
        "completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        execution_time_ms=5000.0
    )
    assert sim_updated.execution_status == "completed"
    assert sim_updated.execution_time_ms == 5000.0


def test_analysis_result_repository(test_session: Session):
    """AnalysisResult Repository 테스트"""
    exp_repo = ExperimentRepository(test_session)
    analysis_repo = AnalysisResultRepository(test_session)

    # Create experiment
    exp = exp_repo.create(id="exp_001", status="pending")

    # Create analysis result
    analysis = analysis_repo.create(
        id="analysis_001",
        experiment_id="exp_001",
        result_json={"kpis": []},
        baseline_kpis={"avg_travel_time": 300.0},
        alternative_kpis=[{"avg_travel_time": 360.0}],
        comparisons=[]
    )

    # Get by experiment
    exp_analysis = analysis_repo.get_by_experiment("exp_001")
    assert exp_analysis is not None
    assert exp_analysis.id == "analysis_001"


def test_report_repository(test_session: Session):
    """Report Repository 테스트"""
    exp_repo = ExperimentRepository(test_session)
    report_repo = ReportRepository(test_session)

    # Create experiment
    exp = exp_repo.create(id="exp_001", status="pending")

    # Create reports
    template_report = report_repo.create(
        id="report_001",
        experiment_id="exp_001",
        report_type="template",
        report_markdown_uri="s3://bucket/report_template.md",
        summary="Template report"
    )
    llm_report = report_repo.create(
        id="report_002",
        experiment_id="exp_001",
        report_type="llm",
        report_markdown_uri="s3://bucket/report_llm.md",
        summary="LLM report"
    )

    # Get by experiment
    reports = report_repo.get_by_experiment("exp_001")
    assert len(reports) == 2

    # Get by type
    template = report_repo.get_by_type("exp_001", "template")
    assert template is not None
    assert template.id == "report_001"

    # Get recent
    recent_reports = report_repo.get_recent(limit=10)
    assert len(recent_reports) == 2


def test_agent_log_repository(test_session: Session):
    """AgentLog Repository 테스트"""
    exp_repo = ExperimentRepository(test_session)
    log_repo = AgentLogRepository(test_session)

    # Create experiment
    exp = exp_repo.create(id="exp_001", status="pending")

    # Create logs
    log1 = log_repo.create(
        experiment_id="exp_001",
        step_name="orchestrator",
        agent_type="llm",
        input_data={"query": "test"},
        output_data={"spec": {}},
        tokens_used=1000,
        execution_time_ms=2000.0,
        status="success"
    )
    log2 = log_repo.create(
        experiment_id="exp_001",
        step_name="scenario_builder",
        agent_type="rule_based",
        execution_time_ms=500.0,
        status="success"
    )

    # Get by experiment
    logs = log_repo.get_by_experiment("exp_001")
    assert len(logs) == 2

    # Get by step
    orchestrator_logs = log_repo.get_by_step("orchestrator")
    assert len(orchestrator_logs) == 1

    # Get by status
    success_logs = log_repo.get_by_status("success")
    assert len(success_logs) == 2

    # Get token usage
    total_tokens = log_repo.get_token_usage_by_experiment("exp_001")
    assert total_tokens == 1000

    # Get average execution time
    avg_time = log_repo.get_average_execution_time_by_step("orchestrator")
    assert avg_time == 2000.0


def test_model_version_repository(test_session: Session):
    """ModelVersion Repository 테스트"""
    repo = ModelVersionRepository(test_session)

    # Create
    model1 = repo.create(
        id="model_001",
        model_name="claude-3-sonnet",
        model_provider="bedrock",
        version_tag="20240229",
        is_active=True
    )
    model2 = repo.create(
        id="model_002",
        model_name="gpt-4",
        model_provider="openai",
        version_tag="v1.0",
        is_active=False
    )

    # Get active
    active_models = repo.get_active()
    assert len(active_models) == 1

    # Get by name
    claude_models = repo.get_by_name("claude-3-sonnet")
    assert len(claude_models) == 1

    # Get by provider
    bedrock_models = repo.get_by_provider("bedrock")
    assert len(bedrock_models) == 1

    # Deactivate
    deactivated = repo.deactivate("model_001")
    assert deactivated.is_active is False

    # Activate
    activated = repo.activate("model_002")
    assert activated.is_active is True


def test_prompt_version_repository(test_session: Session):
    """PromptVersion Repository 테스트"""
    repo = PromptVersionRepository(test_session)

    # Create
    prompt1 = repo.create(
        id="prompt_001",
        prompt_name="orchestrator_system",
        version_tag="v1.0",
        prompt_text="You are an AI assistant.",
        prompt_type="system",
        is_active=True
    )
    prompt2 = repo.create(
        id="prompt_002",
        prompt_name="orchestrator_system",
        version_tag="v2.0",
        prompt_text="You are an advanced AI assistant.",
        prompt_type="system",
        is_active=False
    )

    # Get active
    active_prompts = repo.get_active()
    assert len(active_prompts) == 1

    # Get by name
    orchestrator_prompts = repo.get_by_name("orchestrator_system")
    assert len(orchestrator_prompts) == 2

    # Get active by name
    active_orchestrator = repo.get_active_by_name("orchestrator_system")
    assert active_orchestrator is not None
    assert active_orchestrator.id == "prompt_001"

    # Get by type
    system_prompts = repo.get_by_type("system")
    assert len(system_prompts) == 2

    # Deactivate / Activate
    deactivated = repo.deactivate("prompt_001")
    assert deactivated.is_active is False

    activated = repo.activate("prompt_002")
    assert activated.is_active is True


def test_rag_document_repository(test_session: Session):
    """RAGDocument Repository 테스트"""
    repo = RAGDocumentRepository(test_session)

    # Create
    doc1 = repo.create(
        id="doc_001",
        document_uri="s3://bucket/doc1.pdf",
        title="교통 정책 가이드라인",
        category="policy",
        tags=["교통", "정책"],
        content_text="교통 정책 관련 내용...",
        is_active=True
    )
    doc2 = repo.create(
        id="doc_002",
        document_uri="s3://bucket/doc2.pdf",
        title="SUMO 기술 문서",
        category="technical",
        tags=["SUMO", "기술"],
        content_text="SUMO 관련 기술 내용...",
        is_active=True
    )

    # Get active
    active_docs = repo.get_active()
    assert len(active_docs) == 2

    # Get by category
    policy_docs = repo.get_by_category("policy")
    assert len(policy_docs) == 1

    # Search by text
    search_results = repo.search_by_text("교통")
    assert len(search_results) == 1

    # Search by title
    title_results = repo.search_by_title("SUMO")
    assert len(title_results) == 1

    # Deactivate
    deactivated = repo.deactivate("doc_001")
    assert deactivated.is_active is False
