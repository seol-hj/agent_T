"""
FastAPI 통합 예제
"""

import os
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.db.session import setup_database, get_global_db
from common.db.repositories import (
    ExperimentRepository,
    UserRequestRepository,
    AgentLogRepository,
)
from common.db.models import Experiment as ExperimentModel


# Pydantic Schemas
class UserRequestCreate(BaseModel):
    request_text: str
    language: str = "ko"
    user_id: Optional[str] = None


class ExperimentCreate(BaseModel):
    user_request_id: Optional[str] = None
    status: str = "pending"


class ExperimentResponse(BaseModel):
    id: str
    status: str
    user_request_id: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class AgentLogResponse(BaseModel):
    id: int
    experiment_id: Optional[str]
    step_name: str
    status: str
    execution_time_ms: Optional[float]
    tokens_used: Optional[int]

    class Config:
        from_attributes = True


# FastAPI App
app = FastAPI(
    title="Experiment API",
    description="DB Repository 통합 예제",
    version="0.1.0"
)


@app.on_event("startup")
def startup_event():
    """앱 시작 시 데이터베이스 초기화"""
    # SQLite (로컬 테스트)
    setup_database(database_url="sqlite:///./example.db", echo=False)
    print("✓ 데이터베이스 초기화 완료")


@app.get("/")
def root():
    """루트 엔드포인트"""
    return {
        "service": "Experiment API",
        "version": "0.1.0",
        "endpoints": {
            "experiments": "/experiments",
            "user_requests": "/user-requests",
            "agent_logs": "/agent-logs"
        }
    }


@app.post("/user-requests", status_code=201)
def create_user_request(
    request: UserRequestCreate,
    db: Session = Depends(get_global_db)
):
    """사용자 요청 생성"""
    repo = UserRequestRepository(db)

    import uuid
    request_id = f"req_{uuid.uuid4().hex[:8]}"

    user_request = repo.create(
        id=request_id,
        request_text=request.request_text,
        language=request.language,
        user_id=request.user_id
    )

    return {
        "id": user_request.id,
        "request_text": user_request.request_text,
        "created_at": user_request.created_at.isoformat()
    }


@app.post("/experiments", response_model=ExperimentResponse, status_code=201)
def create_experiment(
    experiment: ExperimentCreate,
    db: Session = Depends(get_global_db)
):
    """실험 생성"""
    repo = ExperimentRepository(db)

    import uuid
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"

    exp = repo.create(
        id=exp_id,
        user_request_id=experiment.user_request_id,
        status=experiment.status
    )

    return ExperimentResponse(
        id=exp.id,
        status=exp.status,
        user_request_id=exp.user_request_id,
        created_at=exp.created_at.isoformat()
    )


@app.get("/experiments", response_model=List[ExperimentResponse])
def get_experiments(
    status: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_global_db)
):
    """실험 목록 조회"""
    repo = ExperimentRepository(db)

    if status:
        experiments = repo.get_by_status(status, limit=limit)
    else:
        experiments = repo.get_recent(limit=limit)

    return [
        ExperimentResponse(
            id=exp.id,
            status=exp.status,
            user_request_id=exp.user_request_id,
            created_at=exp.created_at.isoformat()
        )
        for exp in experiments
    ]


@app.get("/experiments/{exp_id}", response_model=ExperimentResponse)
def get_experiment(
    exp_id: str,
    db: Session = Depends(get_global_db)
):
    """실험 상세 조회"""
    repo = ExperimentRepository(db)
    exp = repo.get(exp_id)

    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return ExperimentResponse(
        id=exp.id,
        status=exp.status,
        user_request_id=exp.user_request_id,
        created_at=exp.created_at.isoformat()
    )


@app.patch("/experiments/{exp_id}/status")
def update_experiment_status(
    exp_id: str,
    status: str,
    db: Session = Depends(get_global_db)
):
    """실험 상태 업데이트"""
    repo = ExperimentRepository(db)
    exp = repo.update_status(exp_id, status)

    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return {
        "id": exp.id,
        "status": exp.status,
        "updated_at": exp.updated_at.isoformat()
    }


@app.delete("/experiments/{exp_id}", status_code=204)
def delete_experiment(
    exp_id: str,
    db: Session = Depends(get_global_db)
):
    """실험 삭제"""
    repo = ExperimentRepository(db)
    deleted = repo.delete(exp_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Experiment not found")


@app.get("/experiments/{exp_id}/logs", response_model=List[AgentLogResponse])
def get_experiment_logs(
    exp_id: str,
    db: Session = Depends(get_global_db)
):
    """실험별 Agent 로그 조회"""
    log_repo = AgentLogRepository(db)
    logs = log_repo.get_by_experiment(exp_id)

    return [
        AgentLogResponse(
            id=log.id,
            experiment_id=log.experiment_id,
            step_name=log.step_name,
            status=log.status,
            execution_time_ms=log.execution_time_ms,
            tokens_used=log.tokens_used
        )
        for log in logs
    ]


@app.get("/experiments/{exp_id}/stats")
def get_experiment_stats(
    exp_id: str,
    db: Session = Depends(get_global_db)
):
    """실험 통계"""
    log_repo = AgentLogRepository(db)

    total_tokens = log_repo.get_token_usage_by_experiment(exp_id)
    logs = log_repo.get_by_experiment(exp_id)

    return {
        "experiment_id": exp_id,
        "total_logs": len(logs),
        "total_tokens": total_tokens,
        "steps": [log.step_name for log in logs]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
