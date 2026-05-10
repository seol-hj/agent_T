"""
Dry Run Executor Tests

DryRunSumoExecutor 단위 테스트
"""

import pytest
import tempfile
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from simulator_runner.executors.dry_run_executor import DryRunSumoExecutor


@pytest.fixture
def executor():
    """DryRunSumoExecutor 인스턴스 (지연 비활성화)"""
    return DryRunSumoExecutor(simulate_delay=False)


@pytest.fixture
def temp_work_dir():
    """임시 작업 디렉토리"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.asyncio
async def test_execute_success(executor, temp_work_dir):
    """성공적인 실행 테스트"""
    result = await executor.execute(
        config_file_path=str(temp_work_dir / "simulation.sumocfg"),
        working_directory=str(temp_work_dir),
    )

    assert result.success is True
    assert result.return_code == 0
    assert "DRY RUN" in result.stdout
    assert result.stderr == ""
    assert result.execution_time_ms >= 0
    assert len(result.output_files) == 4


@pytest.mark.asyncio
async def test_output_files_created(executor, temp_work_dir):
    """출력 파일 생성 테스트"""
    result = await executor.execute(
        config_file_path=str(temp_work_dir / "simulation.sumocfg"),
        working_directory=str(temp_work_dir),
    )

    # 모든 출력 파일 확인
    assert "tripinfo" in result.output_files
    assert "summary" in result.output_files
    assert "queue" in result.output_files
    assert "emission" in result.output_files

    # 파일 존재 확인
    for output_type, file_path in result.output_files.items():
        assert Path(file_path).exists()
        assert Path(file_path).stat().st_size > 0


@pytest.mark.asyncio
async def test_tripinfo_xml_content(executor, temp_work_dir):
    """tripinfo.xml 내용 확인"""
    result = await executor.execute(
        config_file_path=str(temp_work_dir / "simulation.sumocfg"),
        working_directory=str(temp_work_dir),
    )

    tripinfo_path = Path(result.output_files["tripinfo"])
    content = tripinfo_path.read_text()

    assert "<?xml version" in content
    assert "<tripinfos" in content
    assert "<tripinfo" in content
    assert "veh_0" in content


@pytest.mark.asyncio
async def test_summary_xml_content(executor, temp_work_dir):
    """summary.xml 내용 확인"""
    result = await executor.execute(
        config_file_path=str(temp_work_dir / "simulation.sumocfg"),
        working_directory=str(temp_work_dir),
    )

    summary_path = Path(result.output_files["summary"])
    content = summary_path.read_text()

    assert "<summary" in content
    assert "<step" in content
    assert "time=" in content


@pytest.mark.asyncio
async def test_queue_xml_content(executor, temp_work_dir):
    """queue.xml 내용 확인"""
    result = await executor.execute(
        config_file_path=str(temp_work_dir / "simulation.sumocfg"),
        working_directory=str(temp_work_dir),
    )

    queue_path = Path(result.output_files["queue"])
    content = queue_path.read_text()

    assert "<queue-export" in content
    assert "<data" in content
    assert "timestep=" in content


@pytest.mark.asyncio
async def test_emission_xml_content(executor, temp_work_dir):
    """emission.xml 내용 확인"""
    result = await executor.execute(
        config_file_path=str(temp_work_dir / "simulation.sumocfg"),
        working_directory=str(temp_work_dir),
    )

    emission_path = Path(result.output_files["emission"])
    content = emission_path.read_text()

    assert "<emission-export" in content
    assert "<timestep" in content
    assert "<vehicle" in content
    assert "CO2=" in content


def test_validate_environment(executor):
    """환경 검증 테스트"""
    is_valid, message = executor.validate_environment()

    assert is_valid is True
    assert "Dry run" in message


@pytest.mark.asyncio
async def test_simulate_delay():
    """실행 지연 시뮬레이션 테스트"""
    executor_with_delay = DryRunSumoExecutor(simulate_delay=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await executor_with_delay.execute(
            config_file_path=str(Path(tmpdir) / "simulation.sumocfg"),
            working_directory=str(tmpdir),
        )

        # 지연이 있으므로 실행 시간이 100ms 이상
        assert result.execution_time_ms >= 100


@pytest.mark.asyncio
async def test_working_directory_created(executor):
    """작업 디렉토리 생성 테스트"""
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir) / "subdir"

        result = await executor.execute(
            config_file_path=str(work_dir / "simulation.sumocfg"),
            working_directory=str(work_dir),
        )

        assert work_dir.exists()
        assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
