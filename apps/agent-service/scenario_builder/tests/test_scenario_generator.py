"""
Scenario Generator Tests

ScenarioGenerator 단위 테스트
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from scenario_builder.services.scenario_generator import ScenarioGenerator


@pytest.fixture
def scenario_generator():
    """ScenarioGenerator 인스턴스"""
    return ScenarioGenerator()


@pytest.fixture
def sample_experiment_spec():
    """샘플 ExperimentSpec"""
    return {
        "experiment_id": "exp-20260507-001",
        "request_id": "req-20260507-123456",
        "title": "강남구 출퇴근 시간대 신호등 최적화 효과 분석",
        "description": "서울 강남구 출퇴근 시간대의 교통 혼잡을 완화하기 위한 신호등 최적화 방안 비교",
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
        "objectives": ["평균 통행 시간 단축", "배출량 감소"],
        "constraints": []
    }


def test_generate_scenarios_demand_increase(scenario_generator, sample_experiment_spec):
    """교통량 증가 시나리오 생성 테스트"""
    output = scenario_generator.generate_scenarios(
        experiment_spec=sample_experiment_spec,
        request_type="demand_increase"
    )

    # ScenarioBuilderOutput 검증
    assert output.experiment_id == "exp-20260507-001"
    assert output.baseline_variant_id.startswith("base-")
    assert len(output.alternative_variant_ids) >= 1
    assert output.processing_time_ms > 0

    # ScenarioPlan 검증
    scenario_plan = output.scenario_plan
    assert scenario_plan["experiment_id"] == "exp-20260507-001"
    assert scenario_plan["baseline"]["variant_type"] == "baseline"
    assert len(scenario_plan["alternatives"]) >= 1
    assert scenario_plan["alternatives"][0]["variant_type"] == "alternative"

    # Alternative 변형 검증 (demand_multiplier)
    alt = scenario_plan["alternatives"][0]
    assert alt["parameters"]["demand_multiplier"] == 1.2  # 20% 증가

    # NetworkBuildRequest 검증
    assert len(output.network_requests) >= 2  # Baseline + Alternative
    net_req = output.network_requests[0]
    assert net_req["experiment_id"] == "exp-20260507-001"
    assert net_req["osm_source"]["type"] == "bbox"

    # DemandBuildRequest 검증
    assert len(output.demand_requests) >= 2  # Baseline + Alternative
    dem_req_baseline = output.demand_requests[0]
    dem_req_alt = output.demand_requests[1]
    assert dem_req_baseline["demand_settings"]["vehicle_count"] == 5000
    assert dem_req_alt["demand_settings"]["vehicle_count"] == 6000  # 20% 증가


def test_generate_scenarios_lane_change(scenario_generator, sample_experiment_spec):
    """차로 변경 시나리오 생성 테스트"""
    output = scenario_generator.generate_scenarios(
        experiment_spec=sample_experiment_spec,
        request_type="lane_change"
    )

    # Alternative 변형 검증
    alt = output.scenario_plan["alternatives"][0]
    assert "lane" in alt["name"].lower() or "차로" in alt["name"]
    assert alt["parameters"]["demand_multiplier"] == 1.0  # 교통량 변화 없음
    assert alt["parameters"]["network_changes"] is not None

    # NetworkBuildRequest에 modifications 포함 확인
    net_req_alt = output.network_requests[1]  # Alternative
    assert net_req_alt["modifications"] is not None
    assert any(mod["type"] == "lane_change" for mod in net_req_alt["modifications"])


def test_generate_scenarios_signal_timing(scenario_generator, sample_experiment_spec):
    """신호 타이밍 변경 시나리오 생성 테스트"""
    output = scenario_generator.generate_scenarios(
        experiment_spec=sample_experiment_spec,
        request_type="signal_timing_change"
    )

    # Alternative 변형 검증
    alt = output.scenario_plan["alternatives"][0]
    assert "신호" in alt["name"] or "signal" in alt["name"].lower()
    assert alt["parameters"]["network_changes"] is not None

    # NetworkBuildRequest에 신호 타이밍 modifications 포함 확인
    net_req_alt = output.network_requests[1]  # Alternative
    assert net_req_alt["modifications"] is not None
    assert any(mod["type"] == "traffic_light" for mod in net_req_alt["modifications"])


def test_create_baseline_variant(scenario_generator, sample_experiment_spec):
    """Baseline 변형 생성 테스트"""
    baseline = scenario_generator._create_baseline_variant(sample_experiment_spec)

    assert baseline["variant_type"] == "baseline"
    assert baseline["variant_id"].startswith("base-")
    assert baseline["parameters"]["demand_multiplier"] == 1.0
    assert baseline["parameters"]["modifications"] == []


def test_create_demand_increase_variant(scenario_generator, sample_experiment_spec):
    """교통량 증가 변형 생성 테스트"""
    variant = scenario_generator._create_demand_increase_variant(
        sample_experiment_spec, suffix="001"
    )

    assert variant["variant_type"] == "alternative"
    assert variant["variant_id"] == "alt-demand-001"
    assert variant["parameters"]["demand_multiplier"] == 1.2


def test_create_lane_change_variant(scenario_generator, sample_experiment_spec):
    """차로 변경 변형 생성 테스트"""
    variant = scenario_generator._create_lane_change_variant(
        sample_experiment_spec, suffix="001"
    )

    assert variant["variant_type"] == "alternative"
    assert variant["variant_id"] == "alt-lane-001"
    assert variant["parameters"]["network_changes"] is not None
    assert "lane_modifications" in variant["parameters"]["network_changes"]


def test_create_signal_timing_variant(scenario_generator, sample_experiment_spec):
    """신호 타이밍 변형 생성 테스트"""
    variant = scenario_generator._create_signal_timing_variant(
        sample_experiment_spec, suffix="001"
    )

    assert variant["variant_type"] == "alternative"
    assert variant["variant_id"] == "alt-signal-001"
    assert variant["parameters"]["network_changes"] is not None
    assert "signal_timing" in variant["parameters"]["network_changes"]


def test_create_network_requests(scenario_generator, sample_experiment_spec):
    """NetworkBuildRequest 생성 테스트"""
    baseline = scenario_generator._create_baseline_variant(sample_experiment_spec)
    alternatives = [
        scenario_generator._create_demand_increase_variant(
            sample_experiment_spec, suffix="001"
        )
    ]

    network_requests = scenario_generator._create_network_requests(
        experiment_spec=sample_experiment_spec,
        baseline=baseline,
        alternatives=alternatives,
    )

    # Baseline + Alternative = 2개
    assert len(network_requests) == 2

    # Baseline 요청 검증
    baseline_req = network_requests[0]
    assert baseline_req["variant_id"] == baseline["variant_id"]
    assert baseline_req["osm_source"]["bbox"] == [127.0276, 37.4959, 127.0948, 37.5219]
    assert baseline_req["modifications"] is None

    # Alternative 요청 검증
    alt_req = network_requests[1]
    assert alt_req["variant_id"] == alternatives[0]["variant_id"]


def test_create_demand_requests(scenario_generator, sample_experiment_spec):
    """DemandBuildRequest 생성 테스트"""
    baseline = scenario_generator._create_baseline_variant(sample_experiment_spec)
    alternatives = [
        scenario_generator._create_demand_increase_variant(
            sample_experiment_spec, suffix="001"
        )
    ]

    demand_requests = scenario_generator._create_demand_requests(
        experiment_spec=sample_experiment_spec,
        baseline=baseline,
        alternatives=alternatives,
        request_type="demand_increase",
    )

    # Baseline + Alternative = 2개
    assert len(demand_requests) == 2

    # Baseline 요청 검증
    baseline_req = demand_requests[0]
    assert baseline_req["variant_id"] == baseline["variant_id"]
    assert baseline_req["demand_settings"]["vehicle_count"] == 5000
    assert baseline_req["demand_settings"]["start_time"] == 25200  # 07:00 → 7*3600

    # Alternative 요청 검증 (20% 증가)
    alt_req = demand_requests[1]
    assert alt_req["variant_id"] == alternatives[0]["variant_id"]
    assert alt_req["demand_settings"]["vehicle_count"] == 6000  # 5000 * 1.2


def test_time_to_seconds(scenario_generator):
    """시간 변환 테스트"""
    assert scenario_generator._time_to_seconds("07:00") == 25200
    assert scenario_generator._time_to_seconds("09:30") == 34200
    assert scenario_generator._time_to_seconds("00:00") == 0
    assert scenario_generator._time_to_seconds(3600) == 3600  # 이미 초


def test_convert_network_modifications(scenario_generator):
    """네트워크 수정사항 변환 테스트"""
    # 차로 변경
    lane_changes = {
        "lane_modifications": {
            "strategy": "increase_major_roads",
            "lane_delta": 1,
        }
    }
    modifications = scenario_generator._convert_network_modifications(lane_changes)
    assert len(modifications) == 1
    assert modifications[0]["type"] == "lane_change"

    # 신호 타이밍 변경
    signal_changes = {
        "signal_timing": {
            "strategy": "optimize_cycle",
            "cycle_seconds": 90,
            "green_time_ratio": 0.55,
        }
    }
    modifications = scenario_generator._convert_network_modifications(signal_changes)
    assert len(modifications) == 1
    assert modifications[0]["type"] == "traffic_light"

    # 두 가지 모두
    combined_changes = {
        "lane_modifications": {"strategy": "increase_major_roads", "lane_delta": 1},
        "signal_timing": {"strategy": "optimize_cycle", "cycle_seconds": 90},
    }
    modifications = scenario_generator._convert_network_modifications(combined_changes)
    assert len(modifications) == 2


def test_all_variants_have_unique_ids(scenario_generator, sample_experiment_spec):
    """모든 변형이 고유 ID를 갖는지 테스트"""
    output = scenario_generator.generate_scenarios(
        experiment_spec=sample_experiment_spec,
        request_type="demand_increase"
    )

    # ScenarioPlan의 모든 변형 ID 수집
    variant_ids = [output.scenario_plan["baseline"]["variant_id"]]
    variant_ids.extend([alt["variant_id"] for alt in output.scenario_plan["alternatives"]])

    # 중복 없는지 확인
    assert len(variant_ids) == len(set(variant_ids))


def test_network_and_demand_requests_match_variants(scenario_generator, sample_experiment_spec):
    """NetworkBuildRequest와 DemandBuildRequest가 변형과 일치하는지 테스트"""
    output = scenario_generator.generate_scenarios(
        experiment_spec=sample_experiment_spec,
        request_type="signal_timing_change"
    )

    # 변형 ID 수집
    variant_ids = [output.scenario_plan["baseline"]["variant_id"]]
    variant_ids.extend([alt["variant_id"] for alt in output.scenario_plan["alternatives"]])

    # NetworkBuildRequest variant_id 검증
    net_variant_ids = [req["variant_id"] for req in output.network_requests]
    assert set(net_variant_ids) == set(variant_ids)

    # DemandBuildRequest variant_id 검증
    dem_variant_ids = [req["variant_id"] for req in output.demand_requests]
    assert set(dem_variant_ids) == set(variant_ids)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
