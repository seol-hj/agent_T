"""
SQLAlchemy ORM Models

모든 테이블 정의
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Experiment(Base):
    """실험 메타데이터"""
    __tablename__ = "experiments"

    id = Column(String(255), primary_key=True)
    user_request_id = Column(String(255), ForeignKey("user_requests.id"), nullable=True)
    experiment_spec_id = Column(String(255), ForeignKey("experiment_specs.id"), nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    user_request = relationship("UserRequest", back_populates="experiments")
    experiment_spec = relationship("ExperimentSpec", back_populates="experiments")
    scenarios = relationship("Scenario", back_populates="experiment", cascade="all, delete-orphan")
    simulation_runs = relationship("SimulationRun", back_populates="experiment", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="experiment", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="experiment", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="experiment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_experiments_status", "status"),
        Index("idx_experiments_created_at", "created_at"),
    )


class UserRequest(Base):
    """사용자 요청 원본"""
    __tablename__ = "user_requests"

    id = Column(String(255), primary_key=True)
    request_text = Column(Text, nullable=False)
    language = Column(String(10), default="ko", nullable=False)
    user_id = Column(String(255), nullable=True)  # 향후 사용자 인증 시
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    experiments = relationship("Experiment", back_populates="user_request")

    __table_args__ = (
        Index("idx_user_requests_created_at", "created_at"),
    )


class ExperimentSpec(Base):
    """실험 명세 (Orchestrator 출력)"""
    __tablename__ = "experiment_specs"

    id = Column(String(255), primary_key=True)
    version = Column(String(50), nullable=False)
    spec_json = Column(JSON, nullable=False)  # ExperimentSpec Pydantic 모델의 JSON
    confidence_score = Column(Float, nullable=True)
    model_version_id = Column(String(255), ForeignKey("model_versions.id"), nullable=True)
    prompt_version_id = Column(String(255), ForeignKey("prompt_versions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    experiments = relationship("Experiment", back_populates="experiment_spec")
    model_version = relationship("ModelVersion")
    prompt_version = relationship("PromptVersion")

    __table_args__ = (
        Index("idx_experiment_specs_created_at", "created_at"),
    )


class Scenario(Base):
    """시나리오 (Baseline + Alternatives)"""
    __tablename__ = "scenarios"

    id = Column(String(255), primary_key=True)
    experiment_id = Column(String(255), ForeignKey("experiments.id"), nullable=False)
    scenario_type = Column(String(50), nullable=False)  # baseline, demand_increase, lane_change, etc.
    plan_json = Column(JSON, nullable=False)  # ScenarioPlan Pydantic 모델의 JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="scenarios")
    network_artifacts = relationship("NetworkArtifact", back_populates="scenario", cascade="all, delete-orphan")
    demand_artifacts = relationship("DemandArtifact", back_populates="scenario", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_scenarios_experiment_id", "experiment_id"),
        Index("idx_scenarios_scenario_type", "scenario_type"),
    )


class NetworkArtifact(Base):
    """네트워크 산출물 (.net.xml)"""
    __tablename__ = "network_artifacts"

    id = Column(String(255), primary_key=True)
    scenario_id = Column(String(255), ForeignKey("scenarios.id"), nullable=False)
    request_id = Column(String(255), nullable=False)
    variant_id = Column(String(255), nullable=False)  # baseline, alt_1, alt_2, etc.
    network_file_uri = Column(String(1024), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scenario = relationship("Scenario", back_populates="network_artifacts")

    __table_args__ = (
        Index("idx_network_artifacts_scenario_id", "scenario_id"),
        Index("idx_network_artifacts_variant_id", "variant_id"),
    )


class DemandArtifact(Base):
    """수요 산출물 (.rou.xml)"""
    __tablename__ = "demand_artifacts"

    id = Column(String(255), primary_key=True)
    scenario_id = Column(String(255), ForeignKey("scenarios.id"), nullable=False)
    request_id = Column(String(255), nullable=False)
    variant_id = Column(String(255), nullable=False)  # baseline, alt_1, alt_2, etc.
    routes_file_uri = Column(String(1024), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scenario = relationship("Scenario", back_populates="demand_artifacts")

    __table_args__ = (
        Index("idx_demand_artifacts_scenario_id", "scenario_id"),
        Index("idx_demand_artifacts_variant_id", "variant_id"),
    )


class SimulationRun(Base):
    """시뮬레이션 실행 기록"""
    __tablename__ = "simulation_runs"

    id = Column(String(255), primary_key=True)
    experiment_id = Column(String(255), ForeignKey("experiments.id"), nullable=False)
    variant_id = Column(String(255), nullable=False)  # baseline, alt_1, alt_2, etc.
    config_file_uri = Column(String(1024), nullable=False)
    output_tripinfo_uri = Column(String(1024), nullable=True)
    output_summary_uri = Column(String(1024), nullable=True)
    output_queue_uri = Column(String(1024), nullable=True)
    output_emission_uri = Column(String(1024), nullable=True)
    execution_status = Column(String(50), nullable=False)  # pending, running, completed, failed
    execution_time_ms = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    experiment = relationship("Experiment", back_populates="simulation_runs")

    __table_args__ = (
        Index("idx_simulation_runs_experiment_id", "experiment_id"),
        Index("idx_simulation_runs_variant_id", "variant_id"),
        Index("idx_simulation_runs_execution_status", "execution_status"),
    )


class AnalysisResult(Base):
    """분석 결과 (KPI + 비교)"""
    __tablename__ = "analysis_results"

    id = Column(String(255), primary_key=True)
    experiment_id = Column(String(255), ForeignKey("experiments.id"), nullable=False)
    result_json = Column(JSON, nullable=False)  # AnalysisResult Pydantic 모델의 JSON
    baseline_kpis = Column(JSON, nullable=False)  # KPIData JSON
    alternative_kpis = Column(JSON, nullable=False)  # List[KPIData] JSON
    comparisons = Column(JSON, nullable=False)  # List[ScenarioComparison] JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="analysis_results")

    __table_args__ = (
        Index("idx_analysis_results_experiment_id", "experiment_id"),
    )


class Report(Base):
    """리포트 산출물"""
    __tablename__ = "reports"

    id = Column(String(255), primary_key=True)
    experiment_id = Column(String(255), ForeignKey("experiments.id"), nullable=False)
    report_type = Column(String(50), nullable=False)  # template, llm
    report_markdown_uri = Column(String(1024), nullable=False)
    report_pdf_uri = Column(String(1024), nullable=True)
    summary = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)  # List[str]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="reports")

    __table_args__ = (
        Index("idx_reports_experiment_id", "experiment_id"),
        Index("idx_reports_report_type", "report_type"),
    )


class AgentLog(Base):
    """Agent 실행 로그"""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(255), ForeignKey("experiments.id"), nullable=True)
    step_name = Column(String(100), nullable=False)  # orchestrator, scenario_builder, etc.
    agent_type = Column(String(100), nullable=True)  # llm, rule_based, etc.
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    model_version_id = Column(String(255), ForeignKey("model_versions.id"), nullable=True)
    prompt_version_id = Column(String(255), ForeignKey("prompt_versions.id"), nullable=True)
    status = Column(String(50), nullable=False)  # success, failure
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="agent_logs")
    model_version = relationship("ModelVersion")
    prompt_version = relationship("PromptVersion")

    __table_args__ = (
        Index("idx_agent_logs_experiment_id", "experiment_id"),
        Index("idx_agent_logs_step_name", "step_name"),
        Index("idx_agent_logs_created_at", "created_at"),
    )


class ModelVersion(Base):
    """LLM 모델 버전 추적"""
    __tablename__ = "model_versions"

    id = Column(String(255), primary_key=True)
    model_name = Column(String(255), nullable=False)  # claude-3-sonnet, gpt-4, etc.
    model_provider = Column(String(100), nullable=False)  # bedrock, openai, etc.
    version_tag = Column(String(100), nullable=False)  # 20240229, v1.0, etc.
    parameters = Column(JSON, nullable=True)  # temperature, max_tokens, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_model_versions_model_name", "model_name"),
        Index("idx_model_versions_is_active", "is_active"),
    )


class PromptVersion(Base):
    """프롬프트 버전 추적"""
    __tablename__ = "prompt_versions"

    id = Column(String(255), primary_key=True)
    prompt_name = Column(String(255), nullable=False)  # orchestrator_system, scenario_builder_user, etc.
    version_tag = Column(String(100), nullable=False)  # v1.0, v2.0, etc.
    prompt_text = Column(Text, nullable=False)
    prompt_type = Column(String(50), nullable=False)  # system, user, assistant
    metadata_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_prompt_versions_prompt_name", "prompt_name"),
        Index("idx_prompt_versions_is_active", "is_active"),
    )


class RAGDocument(Base):
    """RAG 문서 메타데이터"""
    __tablename__ = "rag_documents"

    id = Column(String(255), primary_key=True)
    document_uri = Column(String(1024), nullable=False)
    title = Column(String(512), nullable=True)
    category = Column(String(100), nullable=True)  # policy, technical, case_study, etc.
    tags = Column(JSON, nullable=True)  # List[str]
    content_text = Column(Text, nullable=True)  # 전체 텍스트 (검색용)
    embedding_vector = Column(JSON, nullable=True)  # Vector embedding (향후 벡터 DB로 이동)
    metadata_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_rag_documents_category", "category"),
        Index("idx_rag_documents_is_active", "is_active"),
        Index("idx_rag_documents_created_at", "created_at"),
    )
