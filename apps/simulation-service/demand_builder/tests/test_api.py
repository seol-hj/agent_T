"""
Demand Builder API Tests

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
    storage.upload = AsyncMock(return_value="s3://bucket/test/routes.rou.xml")
    return storage


@pytest.fixture
def app(mock_storage):
    """테스트용 FastAPI 앱"""
    # common 모듈의 get_storage_gateway를 mock
    import common
    original_get_storage = common.get_storage_gateway
    common.get_storage_gateway = lambda: mock_storage

    # 앱 임포트 (startup 이벤트 자동 실행됨)
    from demand_builder.main import app as demand_app

    yield demand_app

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
    assert data["service"] == "demand-builder"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_readiness_check(client):
    """준비 상태 체크 테스트"""
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "demand-builder"
    assert "timestamp" in data


def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "demand-builder"
    assert data["version"] == "0.1.0"
    assert "endpoints" in data
    assert "supported_providers" in data
    assert "supported_vehicle_types" in data

    # Provider 확인
    providers = {p["type"] for p in data["supported_providers"]}
    assert "toy" in providers
    assert "od_matrix" in providers

    # Vehicle types 확인
    assert "passenger" in data["supported_vehicle_types"]
    assert "bus" in data["supported_vehicle_types"]
    assert "truck" in data["supported_vehicle_types"]


def test_build_demand_success(client):
    """교통 수요 빌드 성공 테스트"""
    request_data = {
        "demand_build_request": {
            "schema_version": "1.0",
            "request_id": "req-001",
            "experiment_id": "exp-001",
            "variant_id": "baseline",
            "demand_settings": {
                "provider_type": "toy",
                "vehicle_count": 100,
                "start_time": 0,
                "end_time": 3600,
                "vehicle_types": {
                    "passenger": 1.0
                },
                "trip_distribution": "random",
            }
        }
    }

    response = client.post("/demand/build", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    assert artifact["schema_version"] == "1.0"
    assert artifact["request_id"] == "req-001"
    assert artifact["experiment_id"] == "exp-001"
    assert artifact["variant_id"] == "baseline"
    assert artifact["uri"] == "s3://bucket/test/routes.rou.xml"
    assert artifact["file_format"] == "rou.xml"
    assert artifact["file_size_bytes"] > 0
    assert "statistics" in artifact
    assert artifact["statistics"]["total_vehicles"] == 100
    assert "created_at" in artifact
    assert artifact["generated_by"] == "demand-builder-v0.1.0"


def test_build_demand_multiple_vehicle_types(client):
    """여러 차종 수요 빌드 테스트"""
    request_data = {
        "demand_build_request": {
            "schema_version": "1.0",
            "request_id": "req-002",
            "experiment_id": "exp-002",
            "variant_id": "alternative",
            "demand_settings": {
                "provider_type": "toy",
                "vehicle_count": 100,
                "start_time": 0,
                "end_time": 3600,
                "vehicle_types": {
                    "passenger": 0.8,
                    "bus": 0.1,
                    "truck": 0.1,
                },
            }
        }
    }

    response = client.post("/demand/build", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    stats = artifact["statistics"]
    assert stats["total_vehicles"] == 100
    assert "vehicles_by_type" in stats
    assert "passenger" in stats["vehicles_by_type"]
    assert "bus" in stats["vehicles_by_type"]
    assert "truck" in stats["vehicles_by_type"]


def test_build_demand_with_network_artifact(client):
    """네트워크 아티팩트와 함께 빌드 테스트"""
    request_data = {
        "demand_build_request": {
            "schema_version": "1.0",
            "request_id": "req-003",
            "experiment_id": "exp-003",
            "variant_id": "baseline",
            "demand_settings": {
                "provider_type": "toy",
                "vehicle_count": 50,
                "start_time": 0,
                "end_time": 1800,
                "vehicle_types": {
                    "passenger": 1.0
                },
            }
        },
        "network_artifact": {
            "schema_version": "1.0",
            "artifact_id": "net-001",
            "uri": "s3://bucket/test/network.net.xml",
        }
    }

    response = client.post("/demand/build", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    assert artifact["statistics"]["total_vehicles"] == 50


def test_build_demand_invalid_request(client):
    """잘못된 요청 테스트"""
    # schema_version 누락
    request_data = {
        "demand_build_request": {
            "request_id": "req-004",
            "experiment_id": "exp-004",
            "variant_id": "baseline",
            "demand_settings": {},
        }
    }

    response = client.post("/demand/build", json=request_data)
    assert response.status_code == 500  # Pydantic 검증 실패


def test_build_demand_unsupported_provider(client):
    """지원하지 않는 Provider 테스트"""
    request_data = {
        "demand_build_request": {
            "schema_version": "1.0",
            "request_id": "req-005",
            "experiment_id": "exp-005",
            "variant_id": "baseline",
            "demand_settings": {
                "provider_type": "invalid_provider",
                "vehicle_count": 100,
                "start_time": 0,
                "end_time": 3600,
                "vehicle_types": {
                    "passenger": 1.0
                },
            }
        }
    }

    response = client.post("/demand/build", json=request_data)
    assert response.status_code == 500
    assert "Unsupported provider type" in response.json()["detail"]


def test_build_demand_with_demand_multiplier(client):
    """demand_multiplier 적용 테스트"""
    request_data = {
        "demand_build_request": {
            "schema_version": "1.0",
            "request_id": "req-006",
            "experiment_id": "exp-006",
            "variant_id": "alternative",
            "demand_settings": {
                "provider_type": "toy",
                "vehicle_count": 100,
                "start_time": 0,
                "end_time": 3600,
                "vehicle_types": {
                    "passenger": 1.0
                },
                "demand_multiplier": 1.2,
            }
        }
    }

    response = client.post("/demand/build", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    # vehicle_count가 demand_multiplier를 이미 반영한 값이므로
    # 통계에서도 100이 나와야 함 (multiplier가 중복 적용되지 않음)
    assert artifact["statistics"]["total_vehicles"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
