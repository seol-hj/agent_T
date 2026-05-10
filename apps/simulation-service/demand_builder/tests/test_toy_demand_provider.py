"""
Toy Demand Provider Tests

ToyDemandProvider 단위 테스트
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from demand_builder.providers.toy_demand_provider import ToyDemandProvider


@pytest.fixture
def provider():
    """ToyDemandProvider 인스턴스 (고정 시드)"""
    return ToyDemandProvider(random_seed=42)


@pytest.fixture
def mock_network_data():
    """Mock 네트워크 데이터"""
    class MockNetwork:
        def __init__(self):
            self.edges = [
                {"id": "e_0"},
                {"id": "e_1"},
                {"id": "e_2"},
                {"id": "e_3"},
            ]
    return MockNetwork()


def test_generate_demand_basic(provider, mock_network_data):
    """기본 수요 생성 테스트"""
    demand_config = {
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {"passenger": 1.0},
        "trip_distribution": "random",
    }

    demand_data = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    # 차량 수
    assert len(demand_data.trips) == 100

    # 모든 차량이 passenger
    assert all(t.vehicle_type == "passenger" for t in demand_data.trips)

    # 출발 시간 범위
    assert all(0 <= t.depart_time <= 3600 for t in demand_data.trips)


def test_generate_demand_multiple_vehicle_types(provider, mock_network_data):
    """여러 차종 수요 생성 테스트"""
    demand_config = {
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {
            "passenger": 0.8,
            "bus": 0.1,
            "truck": 0.1,
        },
    }

    demand_data = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    # 차종별 개수
    type_counts = {}
    for trip in demand_data.trips:
        vtype = trip.vehicle_type
        type_counts[vtype] = type_counts.get(vtype, 0) + 1

    assert type_counts["passenger"] == pytest.approx(80, abs=5)
    assert type_counts["bus"] == pytest.approx(10, abs=5)
    assert type_counts["truck"] == pytest.approx(10, abs=5)


def test_generate_demand_uniform_distribution(provider, mock_network_data):
    """균등 분포 출발 시간 테스트"""
    demand_config = {
        "vehicle_count": 10,
        "start_time": 0,
        "end_time": 100,
        "vehicle_types": {"passenger": 1.0},
        "trip_distribution": "uniform",
    }

    demand_data = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    # 출발 시간이 균등하게 분포
    depart_times = sorted([t.depart_time for t in demand_data.trips])
    for i in range(1, len(depart_times)):
        gap = depart_times[i] - depart_times[i-1]
        assert gap == pytest.approx(10, abs=1)  # 100 / 10 = 10


def test_trips_have_different_od(provider, mock_network_data):
    """통행이 서로 다른 OD를 가지는지 테스트"""
    demand_config = {
        "vehicle_count": 50,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {"passenger": 1.0},
    }

    demand_data = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    # 모든 통행이 from != to
    for trip in demand_data.trips:
        assert trip.from_edge != trip.to_edge


def test_vehicle_ids_unique(provider, mock_network_data):
    """차량 ID 고유성 테스트"""
    demand_config = {
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {"passenger": 1.0},
    }

    demand_data = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    vehicle_ids = [t.vehicle_id for t in demand_data.trips]
    assert len(vehicle_ids) == len(set(vehicle_ids))


def test_apply_demand_multiplier_increase(provider, mock_network_data):
    """수요 증가 테스트"""
    demand_config = {
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {"passenger": 1.0},
    }

    original_demand = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    # 20% 증가
    increased_demand = provider.apply_demand_multiplier(
        demand_data=original_demand,
        multiplier=1.2,
    )

    assert len(increased_demand.trips) == 120


def test_apply_demand_multiplier_decrease(provider, mock_network_data):
    """수요 감소 테스트"""
    demand_config = {
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {"passenger": 1.0},
    }

    original_demand = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    # 20% 감소
    decreased_demand = provider.apply_demand_multiplier(
        demand_data=original_demand,
        multiplier=0.8,
    )

    assert len(decreased_demand.trips) == 80


def test_apply_demand_multiplier_no_change(provider, mock_network_data):
    """수요 변경 없음 테스트"""
    demand_config = {
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {"passenger": 1.0},
    }

    original_demand = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    # 변경 없음
    same_demand = provider.apply_demand_multiplier(
        demand_data=original_demand,
        multiplier=1.0,
    )

    assert len(same_demand.trips) == 100


def test_vehicle_type_definitions(provider):
    """차종 정의 테스트"""
    vtypes = provider._get_vehicle_type_definitions()

    assert "passenger" in vtypes
    assert "bus" in vtypes
    assert "truck" in vtypes

    # Passenger 속성
    assert vtypes["passenger"]["length"] == 5.0
    assert vtypes["passenger"]["vClass"] == "passenger"

    # Bus 속성
    assert vtypes["bus"]["length"] == 12.0
    assert vtypes["bus"]["vClass"] == "bus"


def test_assign_vehicle_types(provider):
    """차종 할당 테스트"""
    assignments = provider._assign_vehicle_types(
        vehicle_count=100,
        vehicle_types_ratio={"passenger": 0.8, "bus": 0.1, "truck": 0.1}
    )

    assert assignments["passenger"] == 80
    assert assignments["bus"] == 10
    assert assignments["truck"] == 10
    assert sum(assignments.values()) == 100


def test_statistics(provider, mock_network_data):
    """통계 계산 테스트"""
    demand_config = {
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {"passenger": 0.8, "bus": 0.2},
    }

    demand_data = provider.generate_demand(
        network_data=mock_network_data,
        demand_config=demand_config,
    )

    stats = demand_data.statistics

    assert stats["total_vehicles"] == 100
    assert stats["total_trips"] == 100
    assert "vehicles_by_type" in stats
    assert "departure_time_range" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
