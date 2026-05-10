"""
Analyzer API Tests

FastAPI 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

# Mock StorageGateway
from unittest.mock import AsyncMock


@pytest.fixture
def fixtures_dir():
    """Fixtures 디렉토리 경로"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_storage(fixtures_dir):
    """Mock Storage Gateway"""
    storage = AsyncMock()

    # 파일 다운로드 mock
    def download_side_effect(uri: str):
        if "tripinfo" in uri:
            return (fixtures_dir / "sample_tripinfo.xml").read_bytes()
        elif "summary" in uri:
            return (fixtures_dir / "sample_summary.xml").read_bytes()
        elif "queue" in uri:
            return (fixtures_dir / "sample_queue.xml").read_bytes()
        elif "emission" in uri:
            return (fixtures_dir / "sample_emission.xml").read_bytes()
        else:
            return b"<mock xml/>"

    storage.download = AsyncMock(side_effect=download_side_effect)
    return storage


@pytest.fixture
def app(mock_storage):
    """테스트용 FastAPI 앱"""
    # common 모듈의 get_storage_gateway를 mock
    import common
    original_get_storage = common.get_storage_gateway
    common.get_storage_gateway = lambda: mock_storage

    # 앱 임포트 (startup 이벤트 자동 실행됨)
    from analyzer.main import app as analyzer_app

    yield analyzer_app

    # 원래 함수 복원
    common.get_storage_gateway = original_get_storage


@pytest.fixture
def client(app):
    """테스트 클라이언트"""
    return TestClient(app)


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "analyzer"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_readiness_check(client):
    """준비 상태 체크 테스트"""
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "analyzer"
    assert "timestamp" in data


def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "analyzer"
    assert data["version"] == "0.1.0"
    assert "endpoints" in data
    assert "supported_kpis" in data

    # KPI 확인
    kpi_names = {kpi["name"] for kpi in data["supported_kpis"]}
    assert "average_travel_time" in kpi_names
    assert "average_waiting_time" in kpi_names
    assert "average_speed" in kpi_names
    assert "total_co2" in kpi_names


def test_run_analysis_success(client):
    """분석 실행 성공 테스트"""
    request_data = {
        "analysis_request": {
            "schema_version": "1.0",
            "request_id": "req-ana-001",
            "experiment_id": "exp-001",
            "baseline_simulation": {
                "schema_version": "1.0",
                "artifact_id": "sim-001-baseline",
                "variant_id": "baseline",
                "outputs": {
                    "tripinfo": "s3://bucket/exp-001/baseline/tripinfo.xml",
                    "summary": "s3://bucket/exp-001/baseline/summary.xml",
                    "queue": "s3://bucket/exp-001/baseline/queue.xml",
                    "emission": "s3://bucket/exp-001/baseline/emission.xml",
                }
            },
            "alternative_simulations": [
                {
                    "schema_version": "1.0",
                    "artifact_id": "sim-001-alternative",
                    "variant_id": "alternative",
                    "outputs": {
                        "tripinfo": "s3://bucket/exp-001/alternative/tripinfo.xml",
                        "summary": "s3://bucket/exp-001/alternative/summary.xml",
                        "queue": "s3://bucket/exp-001/alternative/queue.xml",
                        "emission": "s3://bucket/exp-001/alternative/emission.xml",
                    }
                }
            ]
        }
    }

    response = client.post("/analysis/run", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert result["schema_version"] == "1.0"
    assert result["request_id"] == "req-ana-001"
    assert result["experiment_id"] == "exp-001"
    assert "kpi_comparison" in result
    assert "overall_score" in result
    assert "summary" in result
    assert result["analyzed_by"] == "analyzer-v0.1.0"


def test_run_analysis_kpi_comparison(client):
    """KPI 비교 결과 확인"""
    request_data = {
        "analysis_request": {
            "schema_version": "1.0",
            "request_id": "req-ana-002",
            "experiment_id": "exp-002",
            "baseline_simulation": {
                "schema_version": "1.0",
                "artifact_id": "sim-002-baseline",
                "variant_id": "baseline",
                "outputs": {
                    "tripinfo": "s3://bucket/exp-002/baseline/tripinfo.xml",
                    "summary": "s3://bucket/exp-002/baseline/summary.xml",
                    "queue": "s3://bucket/exp-002/baseline/queue.xml",
                    "emission": "s3://bucket/exp-002/baseline/emission.xml",
                }
            },
            "alternative_simulations": [
                {
                    "schema_version": "1.0",
                    "artifact_id": "sim-002-alternative",
                    "variant_id": "alternative",
                    "outputs": {
                        "tripinfo": "s3://bucket/exp-002/alternative/tripinfo.xml",
                        "summary": "s3://bucket/exp-002/alternative/summary.xml",
                        "queue": "s3://bucket/exp-002/alternative/queue.xml",
                        "emission": "s3://bucket/exp-002/alternative/emission.xml",
                    }
                }
            ]
        }
    }

    response = client.post("/analysis/run", json=request_data)
    assert response.status_code == 200

    result = response.json()
    kpi_comparison = result["kpi_comparison"]

    assert "baseline_kpis" in kpi_comparison
    assert "alternative_kpis" in kpi_comparison
    assert "improvements" in kpi_comparison

    # Baseline KPI 확인
    baseline_kpis = kpi_comparison["baseline_kpis"]
    assert "average_travel_time" in baseline_kpis
    assert "average_waiting_time" in baseline_kpis
    assert "average_speed" in baseline_kpis
    assert "completed_vehicle_count" in baseline_kpis
    assert "total_co2" in baseline_kpis


def test_run_analysis_improvements(client):
    """개선율 확인"""
    request_data = {
        "analysis_request": {
            "schema_version": "1.0",
            "request_id": "req-ana-003",
            "experiment_id": "exp-003",
            "baseline_simulation": {
                "schema_version": "1.0",
                "artifact_id": "sim-003-baseline",
                "variant_id": "baseline",
                "outputs": {
                    "tripinfo": "s3://bucket/exp-003/baseline/tripinfo.xml",
                }
            },
            "alternative_simulations": [
                {
                    "schema_version": "1.0",
                    "artifact_id": "sim-003-alternative",
                    "variant_id": "alternative",
                    "outputs": {
                        "tripinfo": "s3://bucket/exp-003/alternative/tripinfo.xml",
                    }
                }
            ]
        }
    }

    response = client.post("/analysis/run", json=request_data)
    assert response.status_code == 200

    result = response.json()
    improvements = result["kpi_comparison"]["improvements"]

    # 개선율이 dict 형태
    assert isinstance(improvements, dict)


def test_run_analysis_without_alternatives(client):
    """Alternative 없이 분석"""
    request_data = {
        "analysis_request": {
            "schema_version": "1.0",
            "request_id": "req-ana-004",
            "experiment_id": "exp-004",
            "baseline_simulation": {
                "schema_version": "1.0",
                "artifact_id": "sim-004-baseline",
                "variant_id": "baseline",
                "outputs": {
                    "tripinfo": "s3://bucket/exp-004/baseline/tripinfo.xml",
                }
            },
            "alternative_simulations": []
        }
    }

    response = client.post("/analysis/run", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert "Alternative 시나리오가 없습니다" in result["summary"]


def test_run_analysis_invalid_request(client):
    """잘못된 요청 테스트"""
    request_data = {
        "analysis_request": {
            "request_id": "req-ana-005",
            # schema_version 누락
        }
    }

    response = client.post("/analysis/run", json=request_data)
    assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
