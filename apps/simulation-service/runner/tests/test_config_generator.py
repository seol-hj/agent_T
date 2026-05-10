"""
Config Generator Tests

SumoConfigGenerator 단위 테스트
"""

import pytest
import xml.etree.ElementTree as ET

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from simulator_runner.services.config_generator import SumoConfigGenerator


@pytest.fixture
def generator():
    """SumoConfigGenerator 인스턴스"""
    return SumoConfigGenerator()


def test_generate_basic_config(generator):
    """기본 설정 파일 생성 테스트"""
    output_files = {
        "tripinfo": "tripinfo.xml",
        "summary": "summary.xml",
    }

    config_xml = generator.generate_config(
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_files=output_files,
    )

    # XML 파싱
    root = ET.fromstring(config_xml)
    assert root.tag == "configuration"

    # Input 섹션
    input_elem = root.find("input")
    assert input_elem is not None
    net_file = input_elem.find("net-file")
    assert net_file.get("value") == "network.net.xml"
    route_files = input_elem.find("route-files")
    assert route_files.get("value") == "routes.rou.xml"

    # Output 섹션
    output_elem = root.find("output")
    assert output_elem is not None
    tripinfo = output_elem.find("tripinfo-output")
    assert tripinfo.get("value") == "tripinfo.xml"
    summary = output_elem.find("summary-output")
    assert summary.get("value") == "summary.xml"


def test_generate_config_with_all_outputs(generator):
    """모든 출력 파일 포함 설정 생성"""
    output_files = {
        "tripinfo": "tripinfo.xml",
        "summary": "summary.xml",
        "queue": "queue.xml",
        "emission": "emission.xml",
    }

    config_xml = generator.generate_config(
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_files=output_files,
    )

    root = ET.fromstring(config_xml)
    output_elem = root.find("output")

    assert output_elem.find("tripinfo-output") is not None
    assert output_elem.find("summary-output") is not None
    assert output_elem.find("queue-output") is not None
    assert output_elem.find("emission-output") is not None


def test_generate_config_with_time_settings(generator):
    """시간 설정 포함 설정 생성"""
    output_files = {"tripinfo": "tripinfo.xml"}

    simulation_settings = {
        "begin": 0,
        "end": 3600,
        "step_length": 0.5,
    }

    config_xml = generator.generate_config(
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_files=output_files,
        simulation_settings=simulation_settings,
    )

    root = ET.fromstring(config_xml)
    time_elem = root.find("time")
    assert time_elem is not None

    begin = time_elem.find("begin")
    assert begin.get("value") == "0"

    end = time_elem.find("end")
    assert end.get("value") == "3600"

    step_length = time_elem.find("step-length")
    assert step_length.get("value") == "0.5"


def test_generate_config_with_processing_options(generator):
    """처리 옵션 포함 설정 생성"""
    output_files = {"tripinfo": "tripinfo.xml"}

    simulation_settings = {
        "collision_action": "remove",
        "time_to_teleport": 600,
    }

    config_xml = generator.generate_config(
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_files=output_files,
        simulation_settings=simulation_settings,
    )

    root = ET.fromstring(config_xml)
    processing_elem = root.find("processing")
    assert processing_elem is not None

    collision = processing_elem.find("collision.action")
    assert collision.get("value") == "remove"

    teleport = processing_elem.find("time-to-teleport")
    assert teleport.get("value") == "600"


def test_generate_config_without_end_time(generator):
    """종료 시간 없이 설정 생성 (모든 차량 완료까지)"""
    output_files = {"tripinfo": "tripinfo.xml"}

    simulation_settings = {
        "begin": 0,
        "step_length": 1.0,
    }

    config_xml = generator.generate_config(
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_files=output_files,
        simulation_settings=simulation_settings,
    )

    root = ET.fromstring(config_xml)
    time_elem = root.find("time")

    begin = time_elem.find("begin")
    assert begin is not None

    end = time_elem.find("end")
    assert end is None  # end가 없어야 함


def test_generate_config_with_report(generator):
    """리포트 섹션 포함 확인"""
    output_files = {"tripinfo": "tripinfo.xml"}

    config_xml = generator.generate_config(
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_files=output_files,
    )

    root = ET.fromstring(config_xml)
    report_elem = root.find("report")
    assert report_elem is not None

    verbose = report_elem.find("verbose")
    assert verbose.get("value") == "true"

    no_step_log = report_elem.find("no-step-log")
    assert no_step_log.get("value") == "false"


def test_generate_default_simulation_settings(generator):
    """기본 시뮬레이션 설정 생성 테스트"""
    settings = generator.generate_default_simulation_settings(
        begin=0,
        end=3600,
        step_length=1.0,
    )

    assert settings["begin"] == 0
    assert settings["end"] == 3600
    assert settings["step_length"] == 1.0
    assert settings["collision_action"] == "warn"
    assert settings["time_to_teleport"] == 300


def test_generate_default_simulation_settings_without_end(generator):
    """종료 시간 없는 기본 설정"""
    settings = generator.generate_default_simulation_settings(
        begin=0,
        step_length=1.0,
    )

    assert settings["begin"] == 0
    assert "end" not in settings
    assert settings["step_length"] == 1.0


def test_prettify_xml(generator):
    """XML 포맷팅 테스트"""
    output_files = {"tripinfo": "tripinfo.xml"}

    config_xml = generator.generate_config(
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_files=output_files,
    )

    # 줄바꿈 확인
    lines = config_xml.split('\n')
    assert len(lines) > 5

    # 들여쓰기 확인
    assert any(line.startswith('  ') for line in lines)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
