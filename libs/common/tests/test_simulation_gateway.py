"""
Simulation Execution Gateway Tests
"""

import pytest
from ..gateways.simulation import (
    get_simulation_gateway,
    DryRunExecutor,
    SimulationResult,
)


@pytest.mark.asyncio
async def test_dryrun_executor():
    """DryRun Executor 테스트"""
    executor = get_simulation_gateway(executor="dryrun")

    assert isinstance(executor, DryRunExecutor)
    assert executor.executor_name == "dryrun"

    # 실행
    result = await executor.execute(
        scenario_config={"duration": 3600},
        network_file="network.net.xml",
        route_file="routes.rou.xml",
        output_dir="/tmp/output",
    )

    assert isinstance(result, SimulationResult)
    assert result.status == "completed"
    assert result.executor == "dryrun"
    assert result.simulation_id.startswith("sim-dryrun-")
    assert result.duration_seconds >= 0
    assert "tripinfo.xml" in result.output_files
    assert "summary.xml" in result.output_files


@pytest.mark.asyncio
async def test_dryrun_get_status():
    """상태 조회 테스트"""
    executor = get_simulation_gateway(executor="dryrun")

    result = await executor.execute(
        scenario_config={},
        network_file="net.xml",
        route_file="rou.xml",
        output_dir="/tmp/out",
    )

    simulation_id = result.simulation_id

    # 상태 조회
    status = await executor.get_status(simulation_id)
    assert status.simulation_id == simulation_id
    assert status.status == "completed"


@pytest.mark.asyncio
async def test_dryrun_nonexistent_simulation():
    """존재하지 않는 시뮬레이션 조회 테스트"""
    executor = get_simulation_gateway(executor="dryrun")

    with pytest.raises(ValueError, match="Simulation not found"):
        await executor.get_status("nonexistent-id")


@pytest.mark.asyncio
async def test_dryrun_cancel():
    """취소 테스트 (DryRun은 즉시 완료되므로 취소 불가)"""
    executor = get_simulation_gateway(executor="dryrun")

    result = await executor.execute(
        scenario_config={},
        network_file="net.xml",
        route_file="rou.xml",
        output_dir="/tmp/out",
    )

    success = await executor.cancel(result.simulation_id)
    assert not success  # DryRun은 취소 불가


@pytest.mark.asyncio
async def test_simulation_result_metadata():
    """SimulationResult 메타데이터 테스트"""
    executor = get_simulation_gateway(executor="dryrun")

    scenario_config = {
        "duration": 7200,
        "vehicles": 1000,
    }

    result = await executor.execute(
        scenario_config=scenario_config,
        network_file="test.net.xml",
        route_file="test.rou.xml",
        output_dir="/tmp/test",
    )

    # 메타데이터 확인
    assert result.metadata is not None
    assert result.metadata["scenario_config"] == scenario_config
    assert result.metadata["network_file"] == "test.net.xml"

    # Dict 변환
    data = result.to_dict()
    assert "simulation_id" in data
    assert "status" in data
    assert "executor" in data
    assert "duration_seconds" in data
    assert "output_files" in data


@pytest.mark.asyncio
async def test_factory_env_var(monkeypatch):
    """환경 변수 기반 Factory 테스트"""
    monkeypatch.setenv("SIMULATION_EXECUTOR", "dryrun")

    executor = get_simulation_gateway()
    assert executor.executor_name == "dryrun"


def test_factory_invalid_executor():
    """잘못된 Executor 테스트"""
    with pytest.raises(ValueError, match="Unknown simulation executor"):
        get_simulation_gateway(executor="invalid_executor")


@pytest.mark.asyncio
async def test_multiple_simulations():
    """여러 시뮬레이션 실행 테스트"""
    executor = get_simulation_gateway(executor="dryrun")

    results = []
    for i in range(5):
        result = await executor.execute(
            scenario_config={"id": i},
            network_file=f"net{i}.xml",
            route_file=f"rou{i}.xml",
            output_dir=f"/tmp/out{i}",
        )
        results.append(result)

    # 모두 다른 ID
    ids = [r.simulation_id for r in results]
    assert len(ids) == len(set(ids))

    # 모두 완료
    for result in results:
        assert result.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
