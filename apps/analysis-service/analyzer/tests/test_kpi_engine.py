"""
KPI Engine Tests

KPIEngine 단위 테스트
"""

import pytest
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from analyzer.parsers.sumo_result_parser import SumoResultParser
from analyzer.services.kpi_engine import KPIEngine


@pytest.fixture
def parser():
    """SumoResultParser 인스턴스"""
    return SumoResultParser()


@pytest.fixture
def kpi_engine():
    """KPIEngine 인스턴스"""
    return KPIEngine()


@pytest.fixture
def fixtures_dir():
    """Fixtures 디렉토리 경로"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def parsed_data(parser, fixtures_dir):
    """파싱된 샘플 데이터"""
    tripinfo_xml = (fixtures_dir / "sample_tripinfo.xml").read_text()
    summary_xml = (fixtures_dir / "sample_summary.xml").read_text()
    queue_xml = (fixtures_dir / "sample_queue.xml").read_text()
    emission_xml = (fixtures_dir / "sample_emission.xml").read_text()

    return {
        "trips": parser.parse_tripinfo(tripinfo_xml),
        "summary_steps": parser.parse_summary(summary_xml),
        "queues": parser.parse_queue(queue_xml),
        "emissions": parser.parse_emission(emission_xml),
    }


def test_calculate_kpis(kpi_engine, parsed_data):
    """전체 KPI 계산 테스트"""
    kpis = kpi_engine.calculate_kpis(
        trips=parsed_data["trips"],
        summary_steps=parsed_data["summary_steps"],
        queues=parsed_data["queues"],
        emissions=parsed_data["emissions"],
    )

    # 주요 KPI 존재 확인
    assert "average_travel_time" in kpis
    assert "average_waiting_time" in kpis
    assert "average_speed" in kpis
    assert "average_queue_length" in kpis
    assert "completed_vehicle_count" in kpis
    assert "total_co2" in kpis
    assert "total_fuel" in kpis


def test_average_travel_time(kpi_engine, parsed_data):
    """평균 통행 시간 계산"""
    kpis = kpi_engine.calculate_kpis(
        trips=parsed_data["trips"],
        summary_steps=[],
        queues=[],
        emissions=[],
    )

    # (120 + 125 + 130) / 3 = 125
    assert kpis["average_travel_time"] == pytest.approx(125.0, abs=0.1)


def test_average_waiting_time(kpi_engine, parsed_data):
    """평균 대기 시간 계산"""
    kpis = kpi_engine.calculate_kpis(
        trips=parsed_data["trips"],
        summary_steps=[],
        queues=[],
        emissions=[],
    )

    # (10 + 12 + 14) / 3 = 12
    assert kpis["average_waiting_time"] == pytest.approx(12.0, abs=0.1)


def test_average_speed(kpi_engine, parsed_data):
    """평균 속도 계산"""
    kpis = kpi_engine.calculate_kpis(
        trips=parsed_data["trips"],
        summary_steps=[],
        queues=[],
        emissions=[],
    )

    # 총 거리 / 총 시간 = (500 + 520 + 540) / (120 + 125 + 130) = 1560 / 375 = 4.16
    assert kpis["average_speed"] == pytest.approx(4.16, abs=0.1)


def test_completed_vehicle_count(kpi_engine, parsed_data):
    """완료 차량 수"""
    kpis = kpi_engine.calculate_kpis(
        trips=parsed_data["trips"],
        summary_steps=[],
        queues=[],
        emissions=[],
    )

    assert kpis["completed_vehicle_count"] == 3


def test_average_queue_length(kpi_engine, parsed_data):
    """평균 대기열 길이"""
    kpis = kpi_engine.calculate_kpis(
        trips=[],
        summary_steps=[],
        queues=parsed_data["queues"],
        emissions=[],
    )

    # (0 + 0 + 25 + 18 + 20 + 14) / 6 = 77 / 6 ≈ 12.83
    assert kpis["average_queue_length"] == pytest.approx(12.83, abs=0.1)


def test_max_queue_length(kpi_engine, parsed_data):
    """최대 대기열 길이"""
    kpis = kpi_engine.calculate_kpis(
        trips=[],
        summary_steps=[],
        queues=parsed_data["queues"],
        emissions=[],
    )

    assert kpis["max_queue_length"] == 25.0


def test_total_co2(kpi_engine, parsed_data):
    """총 CO2 배출량"""
    kpis = kpi_engine.calculate_kpis(
        trips=[],
        summary_steps=[],
        queues=[],
        emissions=parsed_data["emissions"],
    )

    # 2640 + 2850 + 2720 + 2900 + 2780 + 2700 = 16590
    assert kpis["total_co2"] == pytest.approx(16590.0, abs=1.0)


def test_total_fuel(kpi_engine, parsed_data):
    """총 연료 소비"""
    kpis = kpi_engine.calculate_kpis(
        trips=[],
        summary_steps=[],
        queues=[],
        emissions=parsed_data["emissions"],
    )

    # 1137.48 + 1228.91 + 1172.34 + 1250.23 + 1198.76 + 1164.12 = 7151.84
    assert kpis["total_fuel"] == pytest.approx(7151.84, abs=1.0)


def test_simulation_duration(kpi_engine, parsed_data):
    """시뮬레이션 총 시간"""
    kpis = kpi_engine.calculate_kpis(
        trips=[],
        summary_steps=parsed_data["summary_steps"],
        queues=[],
        emissions=[],
    )

    assert kpis["simulation_duration"] == 120.0


def test_empty_data(kpi_engine):
    """빈 데이터로 KPI 계산"""
    kpis = kpi_engine.calculate_kpis(
        trips=[],
        summary_steps=[],
        queues=[],
        emissions=[],
    )

    assert kpis["average_travel_time"] == 0.0
    assert kpis["average_waiting_time"] == 0.0
    assert kpis["completed_vehicle_count"] == 0
    assert kpis["total_co2"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
