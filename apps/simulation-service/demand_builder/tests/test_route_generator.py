"""
Route Generator Tests

RouteGenerator 단위 테스트
"""

import pytest
import xml.etree.ElementTree as ET

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from demand_builder.services.route_generator import RouteGenerator
from demand_builder.providers.demand_provider import DemandData, Trip


@pytest.fixture
def generator():
    """RouteGenerator 인스턴스"""
    return RouteGenerator()


@pytest.fixture
def sample_demand_data():
    """샘플 수요 데이터"""
    vehicle_types = {
        "passenger": {
            "vClass": "passenger",
            "length": 5.0,
            "minGap": 2.5,
            "maxSpeed": 30.0,
            "accel": 2.6,
            "decel": 4.5,
            "sigma": 0.5,
            "color": "1,1,0",
        },
        "bus": {
            "vClass": "bus",
            "length": 12.0,
            "minGap": 3.0,
            "maxSpeed": 25.0,
            "accel": 1.5,
            "decel": 3.5,
            "sigma": 0.3,
            "color": "0,0,1",
        },
    }

    trips = [
        Trip(
            vehicle_id="veh_0",
            from_edge="e_0",
            to_edge="e_1",
            depart_time=0.0,
            vehicle_type="passenger",
        ),
        Trip(
            vehicle_id="veh_1",
            from_edge="e_1",
            to_edge="e_2",
            depart_time=10.5,
            vehicle_type="passenger",
        ),
        Trip(
            vehicle_id="veh_2",
            from_edge="e_0",
            to_edge="e_3",
            depart_time=5.0,
            vehicle_type="bus",
        ),
    ]

    return DemandData(trips=trips, vehicle_types=vehicle_types)


def test_generate_xml_basic(generator, sample_demand_data):
    """기본 XML 생성 테스트"""
    xml_content = generator.generate_xml(sample_demand_data)

    # XML 파싱
    root = ET.fromstring(xml_content)
    assert root.tag == "routes"

    # vType 요소 확인
    vtypes = root.findall("vType")
    assert len(vtypes) == 2

    # trip 요소 확인
    trips = root.findall("trip")
    assert len(trips) == 3


def test_vehicle_types_in_xml(generator, sample_demand_data):
    """차종 정의가 XML에 포함되는지 테스트"""
    xml_content = generator.generate_xml(sample_demand_data)
    root = ET.fromstring(xml_content)

    vtypes = {vt.get("id"): vt for vt in root.findall("vType")}

    # Passenger 차종
    assert "passenger" in vtypes
    passenger = vtypes["passenger"]
    assert passenger.get("vClass") == "passenger"
    assert passenger.get("length") == "5.00"
    assert passenger.get("maxSpeed") == "30.00"

    # Bus 차종
    assert "bus" in vtypes
    bus = vtypes["bus"]
    assert bus.get("vClass") == "bus"
    assert bus.get("length") == "12.00"
    assert bus.get("maxSpeed") == "25.00"


def test_trip_elements_in_xml(generator, sample_demand_data):
    """통행 요소가 XML에 포함되는지 테스트"""
    xml_content = generator.generate_xml(sample_demand_data)
    root = ET.fromstring(xml_content)

    trips = root.findall("trip")
    trip_ids = [t.get("id") for t in trips]

    assert "veh_0" in trip_ids
    assert "veh_1" in trip_ids
    assert "veh_2" in trip_ids

    # 첫 번째 통행 확인
    veh_0 = next(t for t in trips if t.get("id") == "veh_0")
    assert veh_0.get("type") == "passenger"
    assert veh_0.get("depart") == "0.00"
    assert veh_0.get("from") == "e_0"
    assert veh_0.get("to") == "e_1"


def test_trips_sorted_by_depart_time(generator, sample_demand_data):
    """통행이 출발 시간순으로 정렬되는지 테스트"""
    xml_content = generator.generate_xml(sample_demand_data)
    root = ET.fromstring(xml_content)

    # vType 제외하고 trip만 추출
    trips = root.findall("trip")
    depart_times = [float(t.get("depart")) for t in trips]

    # 정렬 확인
    assert depart_times == sorted(depart_times)


def test_xml_prettification(generator, sample_demand_data):
    """XML이 예쁘게 포맷팅되는지 테스트"""
    xml_content = generator.generate_xml(sample_demand_data)

    # 줄바꿈과 들여쓰기 확인
    lines = xml_content.split('\n')
    assert len(lines) > 10  # 여러 줄로 분리됨
    assert any(line.startswith('  ') for line in lines)  # 들여쓰기 존재


def test_statistics_calculation(generator, sample_demand_data):
    """통계 계산 테스트"""
    stats = generator.calculate_statistics(sample_demand_data)

    assert stats["total_vehicles"] == 3
    assert stats["total_trips"] == 3
    assert stats["vehicles_by_type"]["passenger"] == 2
    assert stats["vehicles_by_type"]["bus"] == 1
    assert stats["departure_time_range"] == [0.0, 10.5]
    assert stats["avg_departure_time"] == pytest.approx(5.166666, abs=0.01)


def test_empty_demand_data(generator):
    """빈 수요 데이터 테스트"""
    empty_data = DemandData(trips=[], vehicle_types={})
    xml_content = generator.generate_xml(empty_data)

    root = ET.fromstring(xml_content)
    assert root.tag == "routes"
    assert len(root.findall("trip")) == 0
    assert len(root.findall("vType")) == 0


def test_statistics_empty_demand(generator):
    """빈 수요 통계 테스트"""
    empty_data = DemandData(trips=[], vehicle_types={})
    stats = generator.calculate_statistics(empty_data)

    assert stats["total_vehicles"] == 0
    assert stats["total_trips"] == 0
    assert stats["vehicles_by_type"] == {}
    assert stats["departure_time_range"] == [0, 0]
    assert stats["avg_departure_time"] == 0


def test_trip_with_route_edges():
    """명시적 경로가 있는 통행 테스트"""
    generator = RouteGenerator()

    vehicle_types = {
        "passenger": {
            "vClass": "passenger",
            "length": 5.0,
            "minGap": 2.5,
            "maxSpeed": 30.0,
            "accel": 2.6,
            "decel": 4.5,
            "sigma": 0.5,
            "color": "1,1,0",
        },
    }

    trips = [
        Trip(
            vehicle_id="veh_0",
            from_edge="e_0",
            to_edge="e_3",
            depart_time=0.0,
            vehicle_type="passenger",
            route_edges=["e_0", "e_1", "e_2", "e_3"],
        ),
    ]

    demand_data = DemandData(trips=trips, vehicle_types=vehicle_types)
    xml_content = generator.generate_xml(demand_data)
    root = ET.fromstring(xml_content)

    # route 요소 확인
    routes = root.findall("route")
    assert len(routes) == 1
    route = routes[0]
    assert route.get("id") == "route_veh_0"
    assert route.get("edges") == "e_0 e_1 e_2 e_3"

    # vehicle 요소 확인
    vehicles = root.findall("vehicle")
    assert len(vehicles) == 1
    vehicle = vehicles[0]
    assert vehicle.get("id") == "veh_0"
    assert vehicle.get("route") == "route_veh_0"


def test_sumo_format_validation():
    """SUMO 형식 유효성 테스트"""
    generator = RouteGenerator()

    vehicle_types = {
        "passenger": {
            "vClass": "passenger",
            "length": 5.0,
            "minGap": 2.5,
            "maxSpeed": 30.0,
            "accel": 2.6,
            "decel": 4.5,
            "sigma": 0.5,
            "color": "1,1,0",
        },
    }

    trips = [
        Trip(
            vehicle_id="veh_0",
            from_edge="e_0",
            to_edge="e_1",
            depart_time=0.0,
            vehicle_type="passenger",
        ),
    ]

    demand_data = DemandData(trips=trips, vehicle_types=vehicle_types)
    xml_content = generator.generate_xml(demand_data)

    # XML 파싱 가능 여부
    root = ET.fromstring(xml_content)

    # SUMO 필수 속성 확인
    vtype = root.find("vType")
    assert vtype.get("id") is not None
    assert vtype.get("vClass") is not None
    assert vtype.get("length") is not None

    trip = root.find("trip")
    assert trip.get("id") is not None
    assert trip.get("type") is not None
    assert trip.get("depart") is not None
    assert trip.get("from") is not None
    assert trip.get("to") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
