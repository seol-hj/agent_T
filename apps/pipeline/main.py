"""
Pipeline Service

E2E 파이프라인 실행 서비스 (DB 연동)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import httpx
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# DB 설정
from db.database import create_tables, get_db
from db.models import PipelineExecution

app = FastAPI(
    title="Pipeline Service",
    description="E2E 교통 시뮬레이션 파이프라인 실행",
    version="0.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 URL
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8001")
SIMULATION_SERVICE_URL = os.getenv("SIMULATION_SERVICE_URL", "http://localhost:8005")
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL", "http://localhost:8006")
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://localhost:8007")

# ============================================================================
# Models
# ============================================================================

class PipelineExecutionRequest(BaseModel):
    request_id: str
    user_request: str
    dry_run: bool = False
    skip_steps: List[str] = Field(default_factory=list)

class PipelineStepStatus(BaseModel):
    step_name: str
    status: str  # pending, running, completed, failed, skipped
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    artifact_uri: Optional[str] = None
    error_message: Optional[str] = None

class PipelineExecutionResult(BaseModel):
    schema_version: str = "1.0"
    execution_id: str
    request_id: str
    experiment_id: str
    status: str
    steps: List[PipelineStepStatus]
    report_uri: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    total_duration_ms: Optional[float] = None
    error_message: Optional[str] = None

# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """DB 테이블 생성"""
    print("✓ Pipeline Service 시작")
    print(f"  - Agent Service: {AGENT_SERVICE_URL}")
    print(f"  - Simulation Service: {SIMULATION_SERVICE_URL}")
    print(f"  - Analysis Service: {ANALYSIS_SERVICE_URL}")
    print(f"  - Report Service: {REPORT_SERVICE_URL}")
    
    # DB 테이블 생성
    try:
        create_tables()
        print("✓ Database tables created/verified")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")

# ============================================================================
# Health & Info
# ============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "pipeline",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.4.0"
    }

@app.get("/ready")
async def readiness_check():
    return {
        "status": "ready",
        "service": "pipeline",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# Pipeline Execution
# ============================================================================

@app.post("/pipeline/run", response_model=PipelineExecutionResult)
async def run_pipeline(
    request: PipelineExecutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    파이프라인 실행 (비동기)
    
    즉시 execution_id를 반환하고 백그라운드에서 실행
    """
    # Execution ID 생성
    execution_id = f"exec-{datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f')[:20]}"
    
    # 초기 상태 저장
    steps = [
        {"step_name": "scenario", "status": "pending"},
        {"step_name": "network", "status": "pending"},
        {"step_name": "demand", "status": "pending"},
        {"step_name": "simulation", "status": "pending"},
        {"step_name": "analysis", "status": "pending"},
        {"step_name": "report", "status": "pending"},
    ]
    
    execution = PipelineExecution(
        execution_id=execution_id,
        request_id=request.request_id,
        experiment_id="",
        status="running",
        steps=steps,
        started_at=datetime.utcnow(),
    )
    
    db.add(execution)
    await db.commit()

    print(f"[Pipeline] Created execution: {execution_id}")

    # 백그라운드에서 실행
    background_tasks.add_task(execute_pipeline, execution_id, request)
    print(f"[Pipeline] Background task added for {execution_id}")

    # 즉시 반환
    return execution.to_dict()

@app.get("/pipeline/{execution_id}/status", response_model=PipelineExecutionResult)
async def get_pipeline_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    파이프라인 진행률 조회
    """
    result = await db.execute(
        select(PipelineExecution).where(PipelineExecution.execution_id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution.to_dict()

# ============================================================================
# Background Execution
# ============================================================================

async def execute_pipeline(execution_id: str, request: PipelineExecutionRequest):
    """
    백그라운드에서 실제 파이프라인 실행
    """
    print(f"[Pipeline Background] Starting execution: {execution_id}")
    from db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            # 실행 조회
            result = await db.execute(
                select(PipelineExecution).where(PipelineExecution.execution_id == execution_id)
            )
            execution = result.scalar_one()
            
            # 1. Scenario Builder
            await update_step(db, execution, "scenario", "running")
            scenario_result = await call_scenario_builder(request.user_request)
            await update_step(db, execution, "scenario", "completed", 
                            artifact_uri=scenario_result.get("scenario_uri"))
            
            experiment_id = scenario_result.get("experiment_id", "exp-unknown")
            execution.experiment_id = experiment_id
            await db.commit()
            
            # 2. Network Builder
            await update_step(db, execution, "network", "running")
            network_result = await call_network_builder(experiment_id, scenario_result.get("scenario_id"))
            await update_step(db, execution, "network", "completed",
                            artifact_uri=network_result.get("network_file_uri"))
            
            # 3. Demand Builder
            await update_step(db, execution, "demand", "running")
            demand_result = await call_demand_builder(experiment_id, network_result.get("network_file_uri"))
            await update_step(db, execution, "demand", "completed",
                            artifact_uri=demand_result.get("demand_file_uri"))
            
            # 4. Simulation Runner
            await update_step(db, execution, "simulation", "running")
            sim_result = await call_simulation_runner(experiment_id, network_result, demand_result, request.dry_run)
            await update_step(db, execution, "simulation", "completed",
                            artifact_uri=sim_result.get("output_files", {}).get("tripinfo"))
            
            # 5. Analyzer
            await update_step(db, execution, "analysis", "running")
            analysis_result = await call_analyzer(experiment_id, sim_result)
            await update_step(db, execution, "analysis", "completed")
            
            # 6. Reporter
            await update_step(db, execution, "report", "running")
            report_result = await call_reporter(experiment_id, analysis_result)
            await update_step(db, execution, "report", "completed")
            
            # 완료
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.report_uri = report_result.get("report_uri")
            total_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000
            execution.total_duration_ms = str(total_ms)
            
            await db.commit()
            
        except Exception as e:
            print(f"Pipeline execution failed: {e}")
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            await db.commit()

async def update_step(db: AsyncSession, execution: PipelineExecution, step_name: str, status: str, **kwargs):
    """특정 단계 상태 업데이트"""
    steps = execution.steps or []
    
    for step in steps:
        if step["step_name"] == step_name:
            step["status"] = status
            if status == "running":
                step["started_at"] = datetime.utcnow().isoformat()
            elif status == "completed":
                step["completed_at"] = datetime.utcnow().isoformat()
                if "started_at" in step:
                    started = datetime.fromisoformat(step["started_at"])
                    duration = (datetime.utcnow() - started).total_seconds() * 1000
                    step["duration_ms"] = duration
            
            if "artifact_uri" in kwargs:
                step["artifact_uri"] = kwargs["artifact_uri"]
            if "error_message" in kwargs:
                step["error_message"] = kwargs["error_message"]
    
    execution.steps = steps
    await db.commit()
    await db.refresh(execution)

# ============================================================================
# Service Calls
# ============================================================================

async def call_scenario_builder(user_request: str) -> dict:
    """Scenario Builder 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{AGENT_SERVICE_URL}/scenario/build",
            json={
                "user_request": user_request,
                "experiment_id": f"exp-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            }
        )
        response.raise_for_status()
        return response.json()

async def call_network_builder(experiment_id: str, scenario_id: str) -> dict:
    """Network Builder 호출"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{SIMULATION_SERVICE_URL}/network/build",
            json={
                "experiment_id": experiment_id,
                "scenario_id": scenario_id,
                "location": {"bbox": [126.9, 37.5, 127.0, 37.6]}
            }
        )
        response.raise_for_status()
        return response.json()

async def call_demand_builder(experiment_id: str, network_file_uri: str) -> dict:
    """Demand Builder 호출"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{SIMULATION_SERVICE_URL}/demand/build",
            json={
                "experiment_id": experiment_id,
                "scenario_id": "scenario-001",
                "network_file_uri": network_file_uri,
                "vehicle_count": 100,
                "duration_hours": 1.0
            }
        )
        response.raise_for_status()
        return response.json()

async def call_simulation_runner(experiment_id: str, network_result: dict, demand_result: dict, dry_run: bool) -> dict:
    """Simulation Runner 호출"""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{SIMULATION_SERVICE_URL}/simulation/run",
            json={
                "experiment_id": experiment_id,
                "scenario_id": "scenario-001",
                "network_file_uri": network_result.get("network_file_uri"),
                "demand_file_uri": demand_result.get("demand_file_uri"),
                "duration_seconds": 3600,
                "use_placeholder": dry_run
            }
        )
        response.raise_for_status()
        return response.json()

async def call_analyzer(experiment_id: str, sim_result: dict) -> dict:
    """Analyzer 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{ANALYSIS_SERVICE_URL}/analysis/run",
            json={
                "experiment_id": experiment_id,
                "scenario_id": "scenario-001",
                "simulation_id": sim_result.get("simulation_id"),
                "tripinfo_uri": sim_result.get("output_files", {}).get("tripinfo", ""),
                "summary_uri": sim_result.get("output_files", {}).get("summary", "")
            }
        )
        response.raise_for_status()
        return response.json()

async def call_reporter(experiment_id: str, analysis_result: dict) -> dict:
    """Reporter 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{REPORT_SERVICE_URL}/report/generate",
            json={
                "experiment_id": experiment_id,
                "scenario_id": "scenario-001",
                "analysis_id": analysis_result.get("analysis_id"),
                "kpis": analysis_result.get("kpis", {})
            }
        )
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
