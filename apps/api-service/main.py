"""
API Service - Health Check Placeholder
교통 시뮬레이션 실험 API의 최소 구현
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

app = FastAPI(
    title="Agent T - API Service",
    description="교통 시뮬레이션 실험 관리 API",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness probe"""
    return {
        "status": "healthy",
        "service": "api-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes readiness probe"""
    # TODO: 실제로는 DB, Redis 연결 확인
    return {
        "status": "ready",
        "service": "api-service",
        "dependencies": {
            "database": "not_configured",
            "redis": "not_configured"
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "api-service",
        "description": "교통 시뮬레이션 실험 관리 API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs"
        },
        "environment": os.getenv("ENV", "dev")
    }

@app.get("/api/experiments")
async def list_experiments():
    """실험 목록 조회 (placeholder)"""
    return {
        "experiments": [],
        "total": 0,
        "message": "실험 관리 기능은 구현 예정입니다"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
