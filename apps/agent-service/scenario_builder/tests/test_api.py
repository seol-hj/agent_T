"""
Scenario Builder API Tests

FastAPI 엔드포인트 통합 테스트
"""

import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from scenario_builder.main import app


@pytest.fixture
def client():
    """TestClient 인스턴스"""
    return TestClient(app)


@pytest.fixture
def sample_experiment_spec():
    """샘플 ExperimentSpec"""
    return {
        "experiment_id": "exp-20260507-001",
        "request_id": "req-20260507-123456",
        "title": "강남구 신호등 최적화",
        "description": "출퇴근 시간대 교통 혼잡 완화",
        "location": {
            "region": "서울특별시 강남구",
            "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
            "osm_query": "Gangnam-gu, Seoul, South Korea"
        },
        "time_settings": {
            "start_time": "07:00",
            "end_time": "09:00",
            "duration_hours": 2,
            "time_period": "weekday_morning_rush"
        },
        "traffic_settings": {
            "vehicle_count": 5000,
            "vehicle_types": ["passenger", "bus", "truck"],
            "vehicle_distribution": {"passenger": 0.8, "bus": 0.1, "truck": 0.1},
            "demand_level": "high"
        },
        "objectives": ["통행 시간 단축", "배출량 감소"],
        "constraints": []
    }


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "scenario-builder"


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
    assert data["service"] == "scenario-builder"
    assert "supported_request_types" in data
    assert len(data["supported_request_types"]) == 3


def test_build_scenarios_demand_increase(client, sample_experiment_spec):
    """교통량 증가 시나리오 빌드 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": sample_experiment_spec,
            "request_type": "demand_increase"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # ScenarioBuilderOutput 검증
    assert data["experiment_id"] == "exp-20260507-001"
    assert "baseline_variant_id" in data
    assert len(data["alternative_variant_ids"]) >= 1
    assert data["processing_time_ms"] > 0

    # ScenarioPlan 검증
    assert "scenario_plan" in data
    scenario_plan = data["scenario_plan"]
    assert scenario_plan["baseline"]["variant_type"] == "baseline"
    assert len(scenario_plan["alternatives"]) >= 1

    # NetworkBuildRequest 검증
    assert "network_requests" in data
    assert len(data["network_requests"]) >= 2

    # DemandBuildRequest 검증
    assert "demand_requests" in data
    assert len(data["demand_requests"]) >= 2


def test_build_scenarios_lane_change(client, sample_experiment_spec):
    """차로 변경 시나리오 빌드 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": sample_experiment_spec,
            "request_type": "lane_change"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Alternative에 network_changes 포함 확인
    alt = data["scenario_plan"]["alternatives"][0]
    assert alt["parameters"]["network_changes"] is not None


def test_build_scenarios_signal_timing(client, sample_experiment_spec):
    """신호 타이밍 변경 시나리오 빌드 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": sample_experiment_spec,
            "request_type": "signal_timing_change"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Alternative에 신호 타이밍 수정 포함 확인
    alt = data["scenario_plan"]["alternatives"][0]
    assert alt["parameters"]["network_changes"] is not None
    assert "signal_timing" in alt["parameters"]["network_changes"]


def test_build_scenarios_invalid_request_type(client, sample_experiment_spec):
    """잘못된 요청 타입 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": sample_experiment_spec,
            "request_type": "invalid_type"
        }
    )

    assert response.status_code == 400
    assert "Unsupported request type" in response.json()["detail"]


def test_build_scenarios_invalid_experiment_spec(client):
    """잘못된 ExperimentSpec 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": {
                "experiment_id": "exp-001",
                # 필수 필드 누락
            },
            "request_type": "demand_increase"
        }
    )

    assert response.status_code == 500  # Pydantic 검증 오류


def test_build_scenarios_missing_fields(client):
    """필수 필드 누락 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": {"experiment_id": "exp-001"},
            # request_type 누락
        }
    )

    assert response.status_code == 422  # FastAPI 검증 오류


def test_demand_multiplier_applied_correctly(client, sample_experiment_spec):
    """교통량 증가율이 올바르게 적용되는지 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": sample_experiment_spec,
            "request_type": "demand_increase"
        }
    )

    data = response.json()

    # Baseline 수요
    baseline_demand = data["demand_requests"][0]["demand_settings"]["vehicle_count"]
    assert baseline_demand == 5000

    # Alternative 수요 (20% 증가)
    alt_demand = data["demand_requests"][1]["demand_settings"]["vehicle_count"]
    assert alt_demand == 6000


def test_network_modifications_for_lane_change(client, sample_experiment_spec):
    """차로 변경 시 네트워크 수정사항 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": sample_experiment_spec,
            "request_type": "lane_change"
        }
    )

    data = response.json()

    # Baseline: modifications 없음
    baseline_net = data["network_requests"][0]
    assert baseline_net["modifications"] is None

    # Alternative: modifications 있음
    alt_net = data["network_requests"][1]
    assert alt_net["modifications"] is not None
    assert any(mod["type"] == "lane_change" for mod in alt_net["modifications"])


def test_all_requests_have_matching_variant_ids(client, sample_experiment_spec):
    """모든 요청이 변형 ID와 일치하는지 테스트"""
    response = client.post(
        "/scenario-builder/build",
        json={
            "experiment_spec": sample_experiment_spec,
            "request_type": "demand_increase"
        }
    )

    data = response.json()

    # 변형 ID 수집
    variant_ids = [data["baseline_variant_id"]]
    variant_ids.extend(data["alternative_variant_ids"])

    # NetworkBuildRequest variant_id
    net_variant_ids = [req["variant_id"] for req in data["network_requests"]]
    assert set(net_variant_ids) == set(variant_ids)

    # DemandBuildRequest variant_id
    dem_variant_ids = [req["variant_id"] for req in data["demand_requests"]]
    assert set(dem_variant_ids) == set(variant_ids)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
