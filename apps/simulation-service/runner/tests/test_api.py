"""
Simulator Runner API Tests

FastAPI 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

# Mock StorageGateway
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_storage():
    """Mock Storage Gateway"""
    storage = AsyncMock()
    storage.download = AsyncMock(return_value=b"<mock xml content/>")
    storage.upload = AsyncMock(side_effect=lambda file_path, content: f"s3://bucket/{file_path}")
    return storage


@pytest.fixture
def app(mock_storage):
    """테스트용 FastAPI 앱"""
    # 환경 변수 설정
    os.environ["SUMO_EXECUTOR"] = "dry_run"

    # common 모듈의 get_storage_gateway를 mock
    import common
    original_get_storage = common.get_storage_gateway
    common.get_storage_gateway = lambda: mock_storage

    # 앱 임포트 (startup 이벤트 자동 실행됨)
    from simulator_runner.main import app as sim_app

    yield sim_app

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
    assert data["service"] == "simulator-runner"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_readiness_check(client):
    """준비 상태 체크 테스트"""
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "simulator-runner"
    assert "timestamp" in data


def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "simulator-runner"
    assert data["version"] == "0.1.0"
    assert "endpoints" in data
    assert "executor_type" in data
    assert "supported_executors" in data
    assert "output_files" in data

    # Executor 확인
    executors = {e["type"] for e in data["supported_executors"]}
    assert "dry_run" in executors
    assert "local" in executors
    assert "k8s" in executors

    # 출력 파일 확인
    assert "tripinfo.xml" in data["output_files"]
    assert "summary.xml" in data["output_files"]
    assert "queue.xml" in data["output_files"]
    assert "emission.xml" in data["output_files"]


def test_run_simulation_success(client):
    """시뮬레이션 실행 성공 테스트"""
    request_data = {
        "simulation_run_request": {
            "schema_version": "1.0",
            "request_id": "req-sim-001",
            "experiment_id": "exp-001",
            "variant_id": "baseline",
            "network_artifact": {
                "schema_version": "1.0",
                "artifact_id": "net-001",
                "uri": "s3://bucket/exp-001/baseline/network.net.xml",
            },
            "demand_artifact": {
                "schema_version": "1.0",
                "artifact_id": "dem-001",
                "uri": "s3://bucket/exp-001/baseline/routes.rou.xml",
            },
            "simulation_settings": {
                "begin": 0,
                "step_length": 1.0,
            }
        }
    }

    response = client.post("/simulation/run", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    assert artifact["schema_version"] == "1.0"
    assert artifact["request_id"] == "req-sim-001"
    assert artifact["experiment_id"] == "exp-001"
    assert artifact["variant_id"] == "baseline"
    assert artifact["status"] == "completed"
    assert "outputs" in artifact
    assert "statistics" in artifact
    assert "execution_time_ms" in artifact
    assert artifact["generated_by"] == "simulator-runner-v0.1.0"


def test_run_simulation_with_all_outputs(client):
    """모든 출력 파일 생성 확인"""
    request_data = {
        "simulation_run_request": {
            "schema_version": "1.0",
            "request_id": "req-sim-002",
            "experiment_id": "exp-002",
            "variant_id": "alternative",
            "network_artifact": {
                "schema_version": "1.0",
                "artifact_id": "net-002",
                "uri": "s3://bucket/exp-002/alternative/network.net.xml",
            },
            "demand_artifact": {
                "schema_version": "1.0",
                "artifact_id": "dem-002",
                "uri": "s3://bucket/exp-002/alternative/routes.rou.xml",
            }
        }
    }

    response = client.post("/simulation/run", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    outputs = artifact["outputs"]

    # 모든 출력 파일 확인
    assert "tripinfo" in outputs
    assert "summary" in outputs
    assert "queue" in outputs
    assert "emission" in outputs


def test_run_simulation_with_custom_settings(client):
    """사용자 정의 설정으로 실행"""
    request_data = {
        "simulation_run_request": {
            "schema_version": "1.0",
            "request_id": "req-sim-003",
            "experiment_id": "exp-003",
            "variant_id": "baseline",
            "network_artifact": {
                "schema_version": "1.0",
                "artifact_id": "net-003",
                "uri": "s3://bucket/exp-003/baseline/network.net.xml",
            },
            "demand_artifact": {
                "schema_version": "1.0",
                "artifact_id": "dem-003",
                "uri": "s3://bucket/exp-003/baseline/routes.rou.xml",
            },
            "simulation_settings": {
                "begin": 0,
                "end": 3600,
                "step_length": 0.5,
                "collision_action": "remove",
                "time_to_teleport": 600,
            }
        }
    }

    response = client.post("/simulation/run", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    assert artifact["status"] == "completed"


def test_run_simulation_invalid_request(client):
    """잘못된 요청 테스트"""
    request_data = {
        "simulation_run_request": {
            "request_id": "req-sim-004",
            "experiment_id": "exp-004",
            # schema_version 누락
        }
    }

    response = client.post("/simulation/run", json=request_data)
    assert response.status_code == 500


def test_run_simulation_statistics(client):
    """통계 정보 확인"""
    request_data = {
        "simulation_run_request": {
            "schema_version": "1.0",
            "request_id": "req-sim-005",
            "experiment_id": "exp-005",
            "variant_id": "baseline",
            "network_artifact": {
                "schema_version": "1.0",
                "artifact_id": "net-005",
                "uri": "s3://bucket/exp-005/baseline/network.net.xml",
            },
            "demand_artifact": {
                "schema_version": "1.0",
                "artifact_id": "dem-005",
                "uri": "s3://bucket/exp-005/baseline/routes.rou.xml",
            }
        }
    }

    response = client.post("/simulation/run", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    stats = artifact["statistics"]

    # 파일 크기 통계 확인
    assert "tripinfo_size_bytes" in stats
    assert "summary_size_bytes" in stats
    assert "queue_size_bytes" in stats
    assert "emission_size_bytes" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
