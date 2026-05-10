"""
Toy Network Provider Tests

ToyNetworkProvider 단위 테스트
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from network_builder.providers.toy_network_provider import ToyNetworkProvider


@pytest.fixture
def provider():
    """ToyNetworkProvider 인스턴스"""
    return ToyNetworkProvider()


def test_generate_network_basic(provider):
    """기본 그리드 생성 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
        network_options={"default_lanes": 2, "default_speed": 13.89},
    )

    # 노드 개수: 3x3 = 9
    assert len(network_data.nodes) == 9

    # 엣지 개수: (3-1)*3*2 + 3*(3-1)*2 = 12 + 12 = 24
    assert len(network_data.edges) == 24

    # 연결 존재
    assert len(network_data.connections) > 0

    # 신호등 (내부 노드만: 1x1 = 1)
    assert len(network_data.traffic_lights) == 1


def test_generate_network_custom_grid(provider):
    """사용자 정의 그리드 크기 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [4, 5]},
    )

    # 노드 개수: 4x5 = 20
    assert len(network_data.nodes) == 20

    # 엣지 개수: (4-1)*5*2 + 4*(5-1)*2 = 30 + 32 = 62
    assert len(network_data.edges) == 62


def test_nodes_have_correct_structure(provider):
    """노드 구조 검증"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
    )

    for node in network_data.nodes:
        assert "id" in node
        assert "x" in node
        assert "y" in node
        assert "type" in node
        assert node["type"] in ["traffic_light", "priority"]


def test_edges_have_correct_structure(provider):
    """엣지 구조 검증"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
    )

    for edge in network_data.edges:
        assert "id" in edge
        assert "from" in edge
        assert "to" in edge
        assert "lanes" in edge
        assert "speed" in edge
        assert "length" in edge
        assert edge["lanes"] == 2
        assert edge["speed"] == 13.89
        assert edge["length"] == 200.0


def test_traffic_lights_generated(provider):
    """신호등 생성 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
        network_options={"tls_guess": True},
    )

    assert len(network_data.traffic_lights) > 0

    for tl in network_data.traffic_lights:
        assert "id" in tl
        assert "junction" in tl
        assert "phases" in tl
        assert len(tl["phases"]) > 0


def test_traffic_lights_disabled(provider):
    """신호등 비활성화 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
        network_options={"tls_guess": False},
    )

    assert network_data.traffic_lights is None


def test_apply_lane_change_increase_all(provider):
    """차로 변경 적용 테스트 (모두 증가)"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
    )

    original_lanes = network_data.edges[0]["lanes"]

    modified_data = provider.apply_modifications(
        network_data=network_data,
        modifications=[
            {
                "type": "lane_change",
                "strategy": "increase_all",
                "lane_delta": 1,
            }
        ],
    )

    # 모든 엣지의 차로 수 증가
    for edge in modified_data.edges:
        assert edge["lanes"] == original_lanes + 1


def test_apply_lane_change_increase_major(provider):
    """차로 변경 적용 테스트 (주요 도로만)"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
    )

    modified_data = provider.apply_modifications(
        network_data=network_data,
        modifications=[
            {
                "type": "lane_change",
                "strategy": "increase_major_roads",
                "lane_delta": 1,
            }
        ],
    )

    # 일부 엣지는 차로 수 증가, 일부는 유지 (길이에 따라)
    lanes_increased = any(e["lanes"] == 3 for e in modified_data.edges)
    assert lanes_increased


def test_apply_speed_change(provider):
    """속도 변경 적용 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
    )

    original_speed = network_data.edges[0]["speed"]

    modified_data = provider.apply_modifications(
        network_data=network_data,
        modifications=[
            {
                "type": "speed_change",
                "strategy": "increase_all",
                "speed_multiplier": 1.2,
            }
        ],
    )

    # 모든 엣지의 속도 증가
    for edge in modified_data.edges:
        assert edge["speed"] == pytest.approx(original_speed * 1.2)


def test_apply_traffic_light_change(provider):
    """신호등 타이밍 변경 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
        network_options={"tls_guess": True},
    )

    modified_data = provider.apply_modifications(
        network_data=network_data,
        modifications=[
            {
                "type": "traffic_light",
                "cycle_seconds": 90,
                "green_time_ratio": 0.55,
            }
        ],
    )

    # 신호등 phase duration 확인
    for tl in modified_data.traffic_lights:
        total_duration = sum(p["duration"] for p in tl["phases"])
        assert total_duration == 90


def test_apply_multiple_modifications(provider):
    """여러 수정사항 동시 적용 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
    )

    modified_data = provider.apply_modifications(
        network_data=network_data,
        modifications=[
            {
                "type": "lane_change",
                "strategy": "increase_all",
                "lane_delta": 1,
            },
            {
                "type": "speed_change",
                "strategy": "increase_all",
                "speed_multiplier": 1.1,
            },
        ],
    )

    # 차로 수 및 속도 모두 변경
    assert modified_data.edges[0]["lanes"] == 3
    assert modified_data.edges[0]["speed"] == pytest.approx(13.89 * 1.1)


def test_network_statistics(provider):
    """도로망 통계 테스트"""
    network_data = provider.generate_network(
        source_config={"type": "toy", "grid_size": [3, 3]},
    )

    stats = network_data.statistics

    assert stats["nodes"] == 9
    assert stats["edges"] == 24
    assert stats["traffic_lights"] == 1
    assert stats["total_length_km"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
