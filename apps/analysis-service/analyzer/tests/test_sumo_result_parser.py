"""
SUMO Result Parser Tests

SumoResultParser 단위 테스트
"""

import pytest
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from analyzer.parsers.sumo_result_parser import SumoResultParser


@pytest.fixture
def parser():
    """SumoResultParser 인스턴스"""
    return SumoResultParser()


@pytest.fixture
def fixtures_dir():
    """Fixtures 디렉토리 경로"""
    return Path(__file__).parent / "fixtures"


def test_parse_tripinfo(parser, fixtures_dir):
    """tripinfo.xml 파싱 테스트"""
    xml_path = fixtures_dir / "sample_tripinfo.xml"
    xml_content = xml_path.read_text()

    trips = parser.parse_tripinfo(xml_content)

    assert len(trips) == 3

    # 첫 번째 차량
    trip_0 = trips[0]
    assert trip_0.vehicle_id == "veh_0"
    assert trip_0.depart_time == 0.0
    assert trip_0.arrival_time == 120.0
    assert trip_0.duration == 120.0
    assert trip_0.route_length == 500.0
    assert trip_0.waiting_time == 10.0
    assert trip_0.waiting_count == 2
    assert trip_0.time_loss == 15.5
    assert trip_0.vehicle_type == "passenger"


def test_parse_tripinfo_empty(parser):
    """빈 tripinfo.xml 파싱"""
    xml_content = '<?xml version="1.0"?><tripinfos></tripinfos>'
    trips = parser.parse_tripinfo(xml_content)
    assert len(trips) == 0


def test_parse_tripinfo_invalid_xml(parser):
    """잘못된 XML 파싱 에러"""
    xml_content = "<invalid xml"
    with pytest.raises(ValueError, match="Failed to parse tripinfo XML"):
        parser.parse_tripinfo(xml_content)


def test_parse_summary(parser, fixtures_dir):
    """summary.xml 파싱 테스트"""
    xml_path = fixtures_dir / "sample_summary.xml"
    xml_content = xml_path.read_text()

    steps = parser.parse_summary(xml_content)

    assert len(steps) == 3

    # 첫 번째 타임스텝
    step_0 = steps[0]
    assert step_0.time == 0.0
    assert step_0.loaded == 10
    assert step_0.inserted == 10
    assert step_0.running == 10
    assert step_0.waiting == 0
    assert step_0.ended == 0
    assert step_0.mean_speed == 10.5


def test_parse_summary_empty(parser):
    """빈 summary.xml 파싱"""
    xml_content = '<?xml version="1.0"?><summary></summary>'
    steps = parser.parse_summary(xml_content)
    assert len(steps) == 0


def test_parse_queue(parser, fixtures_dir):
    """queue.xml 파싱 테스트"""
    xml_path = fixtures_dir / "sample_queue.xml"
    xml_content = xml_path.read_text()

    queues = parser.parse_queue(xml_content)

    assert len(queues) == 6  # 3 timesteps * 2 edges

    # 첫 번째 대기열 데이터
    queue_0 = queues[0]
    assert queue_0.timestep == 0.0
    assert queue_0.edge_id == "e_0"
    assert queue_0.queueing_time == 0.0
    assert queue_0.queueing_length == 0.0

    # 두 번째 타임스텝의 첫 엣지
    queue_2 = [q for q in queues if q.timestep == 60.0 and q.edge_id == "e_0"][0]
    assert queue_2.queueing_length == 25.0


def test_parse_queue_empty(parser):
    """빈 queue.xml 파싱"""
    xml_content = '<?xml version="1.0"?><queue-export></queue-export>'
    queues = parser.parse_queue(xml_content)
    assert len(queues) == 0


def test_parse_emission(parser, fixtures_dir):
    """emission.xml 파싱 테스트"""
    xml_path = fixtures_dir / "sample_emission.xml"
    xml_content = xml_path.read_text()

    emissions = parser.parse_emission(xml_content)

    assert len(emissions) == 6  # 1 + 2 + 3 vehicles

    # 첫 번째 배출 데이터
    emission_0 = emissions[0]
    assert emission_0.timestep == 0.0
    assert emission_0.vehicle_id == "veh_0"
    assert emission_0.co2 == 2640.0
    assert emission_0.co == 164.8
    assert emission_0.fuel == 1137.48


def test_parse_emission_empty(parser):
    """빈 emission.xml 파싱"""
    xml_content = '<?xml version="1.0"?><emission-export></emission-export>'
    emissions = parser.parse_emission(xml_content)
    assert len(emissions) == 0


def test_parse_tripinfo_with_missing_attributes(parser):
    """속성이 누락된 tripinfo 파싱 (기본값 사용)"""
    xml_content = """<?xml version="1.0"?>
    <tripinfos>
        <tripinfo id="veh_0" depart="0.00" arrival="100.00" duration="100.00" routeLength="400.00"/>
    </tripinfos>
    """
    trips = parser.parse_tripinfo(xml_content)

    assert len(trips) == 1
    trip = trips[0]
    assert trip.vehicle_id == "veh_0"
    assert trip.waiting_time == 0.0  # 기본값
    assert trip.waiting_count == 0  # 기본값


def test_parse_summary_with_missing_attributes(parser):
    """속성이 누락된 summary 파싱"""
    xml_content = """<?xml version="1.0"?>
    <summary>
        <step time="0.00" loaded="10" running="10"/>
    </summary>
    """
    steps = parser.parse_summary(xml_content)

    assert len(steps) == 1
    step = steps[0]
    assert step.time == 0.0
    assert step.loaded == 10
    assert step.inserted == 0  # 기본값


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
