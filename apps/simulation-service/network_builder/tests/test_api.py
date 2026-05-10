"""
Network Builder API Tests

FastAPI 엔드포인트 통합 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from network_builder.main import app


@pytest.fixture
def client():
    """TestClient 인스턴스"""
    return TestClient(app)


@pytest.fixture
def sample_network_request():
    """샘플 NetworkBuildRequest"""
    return {
        "schema_version": "1.0",
        "request_id": "netreq-001-base-001",
        "experiment_id": "exp-20260507-001",
        "variant_id": "base-001",
        "osm_source": {
            "type": "toy",
            "grid_size": [3, 3],
        },
        "network_options": {
            "default_lanes": 2,
            "default_speed": 13.89,
            "tls_guess": True,
        },
        "modifications": None,
        "created_at": "2026-05-07T12:00:00Z"
    }


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "network-builder"


def test_ready_check(client):
    """준비 상태 체크 테스트"""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_root(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "network-builder"
    assert "supported_source_types" in data
    assert "supported_modifications" in data


@patch("network_builder.main.network_builder")
def test_build_network_toy(mock_builder, client, sample_network_request):
    """Toy 도로망 빌드 테스트"""
    # Mock 응답
    mock_builder.build_network = AsyncMock(return_value={
        "schema_version": "1.0",
        "artifact_id": "net-001-base-001",
        "request_id": "netreq-001-base-001",
        "experiment_id": "exp-20260507-001",
        "variant_id": "base-001",
        "uri": "file:///app/data/networks/exp-20260507-001/base-001/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 5000,
        "statistics": {
            "nodes": 9,
            "edges": 24,
            "junctions": 9,
            "traffic_lights": 1,
            "total_length_km": 4.8,
        },
        "created_at": "2026-05-07T12:00:00Z",
        "generated_by": "network-builder-v0.1.0",
    })

    response = client.post(
        "/network/build",
        json={
            "network_build_request": sample_network_request
        }
    )

    assert response.status_code == 200
    data = response.json()

    # NetworkArtifact 검증
    assert data["artifact_id"] == "net-001-base-001"
    assert data["experiment_id"] == "exp-20260507-001"
    assert data["variant_id"] == "base-001"
    assert data["file_format"] == "net.xml"
    assert "uri" in data
    assert "statistics" in data


@patch("network_builder.main.network_builder")
def test_build_network_with_lane_change(mock_builder, client, sample_network_request):
    """차로 변경 포함 빌드 테스트"""
    sample_network_request["modifications"] = [
        {
            "type": "lane_change",
            "strategy": "increase_all",
            "lane_delta": 1,
        }
    ]

    mock_builder.build_network = AsyncMock(return_value={
        "artifact_id": "net-001-alt-lane-001",
        "experiment_id": "exp-20260507-001",
        "variant_id": "alt-lane-001",
        "uri": "file:///app/data/networks/exp-20260507-001/alt-lane-001/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 6000,
        "statistics": {"nodes": 9, "edges": 24, "traffic_lights": 1},
        "created_at": "2026-05-07T12:00:00Z",
    })

    response = client.post(
        "/network/build",
        json={
            "network_build_request": sample_network_request
        }
    )

    assert response.status_code == 200


@patch("network_builder.main.network_builder")
def test_build_network_with_speed_change(mock_builder, client, sample_network_request):
    """속도 변경 포함 빌드 테스트"""
    sample_network_request["modifications"] = [
        {
            "type": "speed_change",
            "strategy": "increase_all",
            "speed_multiplier": 1.2,
        }
    ]

    mock_builder.build_network = AsyncMock(return_value={
        "artifact_id": "net-001-base-001",
        "uri": "file:///network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 5000,
        "statistics": {},
        "created_at": "2026-05-07T12:00:00Z",
    })

    response = client.post(
        "/network/build",
        json={
            "network_build_request": sample_network_request
        }
    )

    assert response.status_code == 200


@patch("network_builder.main.network_builder")
def test_build_network_invalid_request(mock_builder, client):
    """잘못된 요청 테스트"""
    response = client.post(
        "/network/build",
        json={
            "network_build_request": {
                "experiment_id": "exp-001",
                # 필수 필드 누락
            }
        }
    )

    assert response.status_code == 500  # Pydantic 검증 오류


def test_build_network_missing_field(client):
    """필수 필드 누락 테스트"""
    response = client.post(
        "/network/build",
        json={
            # network_build_request 누락
        }
    )

    assert response.status_code == 422  # FastAPI 검증 오류


@patch("network_builder.main.network_builder", None)
def test_build_network_service_not_initialized(client, sample_network_request):
    """서비스 미초기화 테스트"""
    response = client.post(
        "/network/build",
        json={
            "network_build_request": sample_network_request
        }
    )

    assert response.status_code == 503


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
