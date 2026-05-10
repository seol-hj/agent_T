"""
SUMO Network Generator Tests

SumoNetworkGenerator 단위 테스트
"""

import pytest
import xml.etree.ElementTree as ET

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from network_builder.providers.network_provider import NetworkData
from network_builder.services.sumo_network_generator import SumoNetworkGenerator


@pytest.fixture
def generator():
    """SumoNetworkGenerator 인스턴스"""
    return SumoNetworkGenerator()


@pytest.fixture
def sample_network_data():
    """샘플 NetworkData"""
    return NetworkData(
        nodes=[
            {"id": "n0", "x": 0.0, "y": 0.0, "type": "priority"},
            {"id": "n1", "x": 200.0, "y": 0.0, "type": "priority"},
        ],
        edges=[
            {
                "id": "e0",
                "from": "n0",
                "to": "n1",
                "lanes": 2,
                "speed": 13.89,
                "length": 200.0,
                "priority": 1,
            }
        ],
        connections=[
            {
                "from": "e0",
                "to": "e0",
                "fromLane": 0,
                "toLane": 0,
            }
        ],
        traffic_lights=None,
    )


def test_generate_xml_basic(generator, sample_network_data):
    """기본 XML 생성 테스트"""
    xml_str = generator.generate_xml(sample_network_data)

    # XML 파싱 가능 확인
    root = ET.fromstring(xml_str)
    assert root.tag == "net"


def test_generate_xml_contains_nodes(generator, sample_network_data):
    """XML에 노드 포함 확인"""
    xml_str = generator.generate_xml(sample_network_data)
    root = ET.fromstring(xml_str)

    junctions = root.findall("junction")
    assert len(junctions) == 2

    junction_ids = [j.get("id") for j in junctions]
    assert "n0" in junction_ids
    assert "n1" in junction_ids


def test_generate_xml_contains_edges(generator, sample_network_data):
    """XML에 엣지 포함 확인"""
    xml_str = generator.generate_xml(sample_network_data)
    root = ET.fromstring(xml_str)

    edges = root.findall("edge")
    assert len(edges) == 1

    edge = edges[0]
    assert edge.get("id") == "e0"
    assert edge.get("from") == "n0"
    assert edge.get("to") == "n1"


def test_generate_xml_contains_lanes(generator, sample_network_data):
    """XML에 lane 포함 확인"""
    xml_str = generator.generate_xml(sample_network_data)
    root = ET.fromstring(xml_str)

    edge = root.find("edge")
    lanes = edge.findall("lane")
    assert len(lanes) == 2  # 2 lanes

    for lane in lanes:
        assert "id" in lane.attrib
        assert "speed" in lane.attrib
        assert "length" in lane.attrib


def test_generate_xml_contains_connections(generator, sample_network_data):
    """XML에 연결 포함 확인"""
    xml_str = generator.generate_xml(sample_network_data)
    root = ET.fromstring(xml_str)

    connections = root.findall("connection")
    assert len(connections) == 1

    conn = connections[0]
    assert conn.get("from") == "e0"
    assert conn.get("to") == "e0"


def test_generate_xml_with_traffic_lights(generator):
    """신호등 포함 XML 생성 테스트"""
    network_data = NetworkData(
        nodes=[
            {"id": "n0", "x": 0.0, "y": 0.0, "type": "traffic_light"},
        ],
        edges=[],
        connections=[],
        traffic_lights=[
            {
                "id": "tl0",
                "junction": "n0",
                "type": "static",
                "programID": "0",
                "offset": 0,
                "phases": [
                    {"duration": 31, "state": "GGrr"},
                    {"duration": 6, "state": "yyrr"},
                ],
            }
        ],
    )

    xml_str = generator.generate_xml(network_data)
    root = ET.fromstring(xml_str)

    tl_logics = root.findall("tlLogic")
    assert len(tl_logics) == 1

    tl = tl_logics[0]
    assert tl.get("id") == "tl0"

    phases = tl.findall("phase")
    assert len(phases) == 2
    assert phases[0].get("duration") == "31"
    assert phases[0].get("state") == "GGrr"


def test_calculate_statistics(generator, sample_network_data):
    """통계 계산 테스트"""
    stats = generator.calculate_statistics(sample_network_data)

    assert stats["nodes"] == 2
    assert stats["edges"] == 1
    assert stats["junctions"] == 2
    assert stats["traffic_lights"] == 0
    assert stats["total_length_km"] == pytest.approx(0.2)
    assert stats["avg_edge_length_m"] == pytest.approx(200.0)


def test_calculate_statistics_with_traffic_lights(generator):
    """신호등 포함 통계 계산 테스트"""
    network_data = NetworkData(
        nodes=[{"id": "n0", "x": 0.0, "y": 0.0, "type": "traffic_light"}],
        edges=[
            {
                "id": "e0",
                "from": "n0",
                "to": "n0",
                "lanes": 2,
                "speed": 13.89,
                "length": 100.0,
                "priority": 1,
            }
        ],
        connections=[],
        traffic_lights=[
            {"id": "tl0", "junction": "n0", "phases": []}
        ],
    )

    stats = generator.calculate_statistics(network_data)
    assert stats["traffic_lights"] == 1


def test_prettify_xml(generator, sample_network_data):
    """XML 포맷팅 테스트"""
    xml_str = generator.generate_xml(sample_network_data)

    # 들여쓰기 확인 (pretty print)
    assert "  " in xml_str  # 들여�기 존재
    assert "\n" in xml_str  # 줄바꿈 존재


def test_xml_is_valid_sumo_format(generator, sample_network_data):
    """SUMO 형식 유효성 테스트"""
    xml_str = generator.generate_xml(sample_network_data)
    root = ET.fromstring(xml_str)

    # 필수 요소 확인
    assert root.find("location") is not None
    assert root.find("junction") is not None
    assert root.find("edge") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
