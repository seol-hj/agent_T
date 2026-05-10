"""
Command Builder Tests

SumoCommandBuilder 단위 테스트
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from simulator_runner.services.command_builder import SumoCommandBuilder


@pytest.fixture
def builder():
    """SumoCommandBuilder 인스턴스"""
    return SumoCommandBuilder(sumo_binary="sumo")


def test_build_basic_command(builder):
    """기본 명령어 생성 테스트"""
    cmd = builder.build_command(config_file="simulation.sumocfg")

    assert cmd == ["sumo", "-c", "simulation.sumocfg"]


def test_build_command_with_gui(builder):
    """GUI 모드 명령어 생성"""
    cmd = builder.build_command(
        config_file="simulation.sumocfg",
        gui=True,
    )

    assert cmd == ["sumo-gui", "-c", "simulation.sumocfg"]


def test_build_command_with_additional_options(builder):
    """추가 옵션 포함 명령어 생성"""
    cmd = builder.build_command(
        config_file="simulation.sumocfg",
        additional_options={
            "verbose": None,
            "no-warnings": None,
            "time-to-teleport": "300",
        }
    )

    assert "sumo" in cmd
    assert "-c" in cmd
    assert "simulation.sumocfg" in cmd
    assert "--verbose" in cmd
    assert "--no-warnings" in cmd
    assert "--time-to-teleport" in cmd
    assert "300" in cmd


def test_build_command_string(builder):
    """명령어 문자열 생성 테스트"""
    cmd_str = builder.build_command_string(
        config_file="simulation.sumocfg",
    )

    assert cmd_str == "sumo -c simulation.sumocfg"


def test_build_command_string_with_options(builder):
    """옵션 포함 명령어 문자열"""
    cmd_str = builder.build_command_string(
        config_file="simulation.sumocfg",
        additional_options={
            "verbose": None,
        }
    )

    assert "sumo" in cmd_str
    assert "-c" in cmd_str
    assert "simulation.sumocfg" in cmd_str
    assert "--verbose" in cmd_str


def test_get_common_options(builder):
    """공통 옵션 반환 테스트"""
    options = builder.get_common_options()

    assert "verbose" in options
    assert "no-step-log" in options
    assert "no-warnings" in options
    assert "time-to-teleport" in options
    assert "collision.action" in options

    assert options["time-to-teleport"] == "300"
    assert options["collision.action"] == "warn"


def test_custom_sumo_binary():
    """사용자 정의 바이너리 경로"""
    builder = SumoCommandBuilder(sumo_binary="/usr/local/bin/sumo")

    cmd = builder.build_command(config_file="simulation.sumocfg")

    assert cmd[0] == "/usr/local/bin/sumo"


def test_additional_options_with_empty_value(builder):
    """빈 값 옵션 처리"""
    cmd = builder.build_command(
        config_file="simulation.sumocfg",
        additional_options={
            "verbose": "",
            "output-prefix": "test_",
        }
    )

    assert "--verbose" in cmd
    assert "--output-prefix" in cmd
    assert "test_" in cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
