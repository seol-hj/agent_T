"""
Scenario Comparator Tests

ScenarioComparator 단위 테스트
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from analyzer.services.scenario_comparator import ScenarioComparator


@pytest.fixture
def comparator():
    """ScenarioComparator 인스턴스"""
    return ScenarioComparator()


@pytest.fixture
def baseline_kpis():
    """Baseline KPI"""
    return {
        "average_travel_time": 125.0,
        "average_waiting_time": 12.0,
        "average_speed": 4.16,
        "average_queue_length": 12.83,
        "completed_vehicle_count": 100,
        "total_co2": 16590.0,
    }


@pytest.fixture
def alternative_kpis_improved():
    """개선된 Alternative KPI"""
    return {
        "average_travel_time": 110.0,  # 12% 개선
        "average_waiting_time": 9.6,   # 20% 개선
        "average_speed": 4.58,          # 10% 개선
        "average_queue_length": 10.26,  # 20% 개선
        "completed_vehicle_count": 100,
        "total_co2": 14931.0,           # 10% 개선
    }


@pytest.fixture
def alternative_kpis_degraded():
    """악화된 Alternative KPI"""
    return {
        "average_travel_time": 137.5,  # 10% 악화
        "average_waiting_time": 14.4,  # 20% 악화
        "average_speed": 3.74,          # 10% 악화
        "average_queue_length": 15.40,  # 20% 악화
        "completed_vehicle_count": 100,
        "total_co2": 18249.0,           # 10% 악화
    }


def test_compare_scenarios_improved(comparator, baseline_kpis, alternative_kpis_improved):
    """개선된 시나리오 비교"""
    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_kpis_improved,
    )

    assert "baseline" in comparison
    assert "alternative" in comparison
    assert "improvements" in comparison

    improvements = comparison["improvements"]

    # 통행 시간 감소 = 개선 (양수)
    assert improvements["average_travel_time"] > 0
    assert improvements["average_travel_time"] == pytest.approx(12.0, abs=0.5)

    # 대기 시간 감소 = 개선 (양수)
    assert improvements["average_waiting_time"] > 0
    assert improvements["average_waiting_time"] == pytest.approx(20.0, abs=0.5)

    # 속도 증가 = 개선 (양수)
    assert improvements["average_speed"] > 0
    assert improvements["average_speed"] == pytest.approx(10.1, abs=0.5)

    # CO2 감소 = 개선 (양수)
    assert improvements["total_co2"] > 0
    assert improvements["total_co2"] == pytest.approx(10.0, abs=0.5)


def test_compare_scenarios_degraded(comparator, baseline_kpis, alternative_kpis_degraded):
    """악화된 시나리오 비교"""
    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_kpis_degraded,
    )

    improvements = comparison["improvements"]

    # 통행 시간 증가 = 악화 (음수)
    assert improvements["average_travel_time"] < 0
    assert improvements["average_travel_time"] == pytest.approx(-10.0, abs=0.5)

    # 대기 시간 증가 = 악화 (음수)
    assert improvements["average_waiting_time"] < 0

    # 속도 감소 = 악화 (음수)
    assert improvements["average_speed"] < 0


def test_improvement_calculation_zero_baseline(comparator):
    """Baseline이 0인 경우 개선율 계산"""
    baseline = {"average_travel_time": 0.0, "average_speed": 10.0}
    alternative = {"average_travel_time": 100.0, "average_speed": 12.0}

    comparison = comparator.compare_scenarios(baseline, alternative)
    improvements = comparison["improvements"]

    # Baseline이 0이면 개선율은 특수 처리 (-100 또는 100)
    assert "average_travel_time" in improvements


def test_calculate_overall_score_improved(comparator, baseline_kpis, alternative_kpis_improved):
    """종합 개선 점수 계산 (개선 시나리오)"""
    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_kpis_improved,
    )

    score = comparator.calculate_overall_score(comparison["improvements"])

    # 모든 지표가 개선되었으므로 양수 점수
    assert score > 0


def test_calculate_overall_score_degraded(comparator, baseline_kpis, alternative_kpis_degraded):
    """종합 개선 점수 계산 (악화 시나리오)"""
    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_kpis_degraded,
    )

    score = comparator.calculate_overall_score(comparison["improvements"])

    # 모든 지표가 악화되었으므로 음수 점수
    assert score < 0


def test_generate_summary_improved(comparator, baseline_kpis, alternative_kpis_improved):
    """개선 시나리오 요약 생성"""
    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_kpis_improved,
    )

    summary = comparator.generate_summary(comparison)

    assert "개선" in summary
    assert "Alternative" in summary


def test_generate_summary_degraded(comparator, baseline_kpis, alternative_kpis_degraded):
    """악화 시나리오 요약 생성"""
    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_kpis_degraded,
    )

    summary = comparator.generate_summary(comparison)

    assert "악화" in summary


def test_generate_summary_mixed(comparator, baseline_kpis):
    """혼합 시나리오 요약 (일부 개선, 일부 악화)"""
    alternative_mixed = {
        "average_travel_time": 110.0,  # 개선
        "average_waiting_time": 15.0,  # 악화
        "average_speed": 4.58,          # 개선
        "average_queue_length": 15.0,   # 악화
        "completed_vehicle_count": 100,
        "total_co2": 16590.0,           # 변화 없음
    }

    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_mixed,
    )

    summary = comparator.generate_summary(comparison)

    assert "개선" in summary or "악화" in summary


def test_generate_summary_no_significant_change(comparator, baseline_kpis):
    """유의미한 변화가 없는 시나리오"""
    alternative_similar = {
        "average_travel_time": 126.0,  # 0.8% 증가
        "average_waiting_time": 12.1,  # 0.8% 증가
        "average_speed": 4.15,          # 0.2% 감소
        "average_queue_length": 12.80,  # 0.2% 감소
        "completed_vehicle_count": 100,
        "total_co2": 16600.0,           # 0.06% 증가
    }

    comparison = comparator.compare_scenarios(
        baseline_kpis=baseline_kpis,
        alternative_kpis=alternative_similar,
    )

    summary = comparator.generate_summary(comparison)

    assert "차이가 크지 않습니다" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
