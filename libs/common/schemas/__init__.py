"""
Common Pydantic Schemas for Agent T Platform

교통 시뮬레이션 플랫폼의 공통 데이터 스키마
모든 서비스 간 데이터 교환에 사용
"""

from .user_request import UserRequest
from .experiment import ExperimentSpec, ScenarioPlan, ScenarioVariant, ScenarioType
from .network import NetworkBuildRequest, NetworkArtifact
from .demand import DemandBuildRequest, DemandArtifact
from .simulation import SimulationRunRequest, SimulationRunArtifact
from .analysis import AnalysisResult, KPIComparison, BaselineKPI, AlternativeKPI
from .report import ReportArtifact, ReportSection
from .logging import AgentLog, LogLevel
from .versioning import ModelVersion, PromptVersion

__all__ = [
    # User
    "UserRequest",

    # Experiment
    "ExperimentSpec",
    "ScenarioPlan",
    "ScenarioVariant",
    "ScenarioType",

    # Network
    "NetworkBuildRequest",
    "NetworkArtifact",

    # Demand
    "DemandBuildRequest",
    "DemandArtifact",

    # Simulation
    "SimulationRunRequest",
    "SimulationRunArtifact",

    # Analysis
    "AnalysisResult",
    "KPIComparison",
    "BaselineKPI",
    "AlternativeKPI",

    # Report
    "ReportArtifact",
    "ReportSection",

    # Logging
    "AgentLog",
    "LogLevel",

    # Versioning
    "ModelVersion",
    "PromptVersion",
]
