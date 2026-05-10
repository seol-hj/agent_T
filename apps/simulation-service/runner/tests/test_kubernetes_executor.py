"""
Kubernetes Job Executor 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from apps.simulatorrunner.executors.kubernetes_executor import KubernetesJobExecutor


@pytest.fixture
def mock_kubernetes_client():
    """Mock Kubernetes client"""
    with patch("apps.simulatorrunner.executors.kubernetes_executor.config") as mock_config, \
         patch("apps.simulatorrunner.executors.kubernetes_executor.client") as mock_client:

        # Mock config
        mock_config.load_incluster_config = Mock()
        mock_config.load_kube_config = Mock()

        # Mock API clients
        mock_batch_v1 = MagicMock()
        mock_core_v1 = MagicMock()

        mock_client.BatchV1Api.return_value = mock_batch_v1
        mock_client.CoreV1Api.return_value = mock_core_v1

        # Mock namespace check
        mock_core_v1.read_namespace.return_value = Mock()

        yield {
            "config": mock_config,
            "client": mock_client,
            "batch_v1": mock_batch_v1,
            "core_v1": mock_core_v1,
        }


@pytest.mark.asyncio
async def test_validate_environment_success(mock_kubernetes_client):
    """환경 검증 성공 테스트"""
    executor = KubernetesJobExecutor(in_cluster=False)

    is_valid, message = executor.validate_environment()

    assert is_valid is True
    assert "validated" in message.lower()
    mock_kubernetes_client["config"].load_kube_config.assert_called_once()


@pytest.mark.asyncio
async def test_validate_environment_incluster(mock_kubernetes_client):
    """클러스터 내부 환경 검증 테스트"""
    executor = KubernetesJobExecutor(in_cluster=True)

    is_valid, message = executor.validate_environment()

    assert is_valid is True
    mock_kubernetes_client["config"].load_incluster_config.assert_called_once()


@pytest.mark.asyncio
async def test_validate_environment_namespace_not_found(mock_kubernetes_client):
    """네임스페이스 없음 에러 테스트"""
    from kubernetes.client.rest import ApiException

    mock_kubernetes_client["core_v1"].read_namespace.side_effect = ApiException(status=404)

    executor = KubernetesJobExecutor(in_cluster=False)
    is_valid, message = executor.validate_environment()

    assert is_valid is False
    assert "not found" in message.lower()


def test_generate_job_name():
    """Job 이름 생성 테스트"""
    executor = KubernetesJobExecutor()

    # 기본 생성
    job_name = executor._generate_job_name(None, None)
    assert job_name.startswith("sumo-sim-")
    assert len(job_name) <= 63

    # experiment_id 포함
    job_name = executor._generate_job_name("exp_001", None)
    assert "exp001" in job_name or "exp" in job_name
    assert len(job_name) <= 63

    # variant_id 포함
    job_name = executor._generate_job_name("exp_001", "baseline")
    assert len(job_name) <= 63

    # 긴 이름 (63자 제한)
    long_exp_id = "a" * 100
    job_name = executor._generate_job_name(long_exp_id, "baseline")
    assert len(job_name) == 63


def test_create_job_manifest(mock_kubernetes_client):
    """Job manifest 생성 테스트"""
    executor = KubernetesJobExecutor(
        namespace="test-ns",
        image="test-image:v1.0",
        storage_gateway_url="http://storage:9002"
    )
    executor.validate_environment()

    job_manifest = executor._create_job_manifest(
        job_name="test-job",
        config_file_uri="s3://bucket/config.sumocfg",
        experiment_id="exp_001",
        scenario_id="scenario_001",
        variant_id="baseline",
        network_artifact_uri="s3://bucket/network.net.xml",
        demand_artifact_uri="s3://bucket/demand.rou.xml",
    )

    # Job 메타데이터 확인
    assert job_manifest.metadata.name == "test-job"
    assert job_manifest.metadata.labels["app"] == "sumo-runner"
    assert job_manifest.metadata.labels["experiment-id"] == "exp_001"

    # Container 확인
    container = job_manifest.spec.template.spec.containers[0]
    assert container.name == "sumo-runner"
    assert container.image == "test-image:v1.0"

    # 환경변수 확인
    env_dict = {env.name: env.value for env in container.env}
    assert env_dict["CONFIG_FILE_URI"] == "s3://bucket/config.sumocfg"
    assert env_dict["EXPERIMENT_ID"] == "exp_001"
    assert env_dict["SCENARIO_ID"] == "scenario_001"
    assert env_dict["VARIANT_ID"] == "baseline"
    assert env_dict["NETWORK_ARTIFACT_URI"] == "s3://bucket/network.net.xml"
    assert env_dict["DEMAND_ARTIFACT_URI"] == "s3://bucket/demand.rou.xml"
    assert env_dict["STORAGE_GATEWAY_URL"] == "http://storage:9002"

    # Pod spec 확인
    assert job_manifest.spec.template.spec.restart_policy == "Never"
    assert job_manifest.spec.template.spec.service_account_name == "sumo-runner"
    assert job_manifest.spec.backoff_limit == 0


@pytest.mark.asyncio
async def test_execute_success(mock_kubernetes_client):
    """Job 실행 성공 테스트"""
    executor = KubernetesJobExecutor(
        namespace="test-ns",
        poll_interval_seconds=0.1,
        timeout_seconds=10,
        in_cluster=False
    )
    executor.validate_environment()

    # Mock Job 생성
    mock_kubernetes_client["batch_v1"].create_namespaced_job.return_value = Mock()

    # Mock Job 상태 (성공)
    mock_job_status = Mock()
    mock_job_status.status.succeeded = 1
    mock_job_status.status.failed = None
    mock_kubernetes_client["batch_v1"].read_namespaced_job_status.return_value = mock_job_status

    # Mock Pod 로그
    mock_pod_list = Mock()
    mock_pod = Mock()
    mock_pod.metadata.name = "test-pod"
    mock_pod_list.items = [mock_pod]
    mock_kubernetes_client["core_v1"].list_namespaced_pod.return_value = mock_pod_list
    mock_kubernetes_client["core_v1"].read_namespaced_pod_log.return_value = "SUMO completed"

    # Mock Job 삭제
    mock_kubernetes_client["batch_v1"].delete_namespaced_job.return_value = Mock()

    # 실행
    result = await executor.execute(
        config_file_path="s3://bucket/config.sumocfg",
        working_directory="/tmp/sumo",
        experiment_id="exp_001",
        variant_id="baseline"
    )

    # 검증
    assert result.success is True
    assert result.return_code == 0
    assert "completed successfully" in result.stdout.lower()
    assert result.execution_time_seconds > 0


@pytest.mark.asyncio
async def test_execute_failure(mock_kubernetes_client):
    """Job 실행 실패 테스트"""
    executor = KubernetesJobExecutor(
        namespace="test-ns",
        poll_interval_seconds=0.1,
        timeout_seconds=10,
        in_cluster=False
    )
    executor.validate_environment()

    # Mock Job 생성
    mock_kubernetes_client["batch_v1"].create_namespaced_job.return_value = Mock()

    # Mock Job 상태 (실패)
    mock_job_status = Mock()
    mock_job_status.status.succeeded = None
    mock_job_status.status.failed = 1
    mock_kubernetes_client["batch_v1"].read_namespaced_job_status.return_value = mock_job_status

    # Mock Pod 로그
    mock_pod_list = Mock()
    mock_pod = Mock()
    mock_pod.metadata.name = "test-pod"
    mock_pod_list.items = [mock_pod]
    mock_kubernetes_client["core_v1"].list_namespaced_pod.return_value = mock_pod_list
    mock_kubernetes_client["core_v1"].read_namespaced_pod_log.return_value = "SUMO failed"

    # Mock Job 삭제
    mock_kubernetes_client["batch_v1"].delete_namespaced_job.return_value = Mock()

    # 실행
    result = await executor.execute(
        config_file_path="s3://bucket/config.sumocfg",
        working_directory="/tmp/sumo",
        experiment_id="exp_001",
        variant_id="baseline"
    )

    # 검증
    assert result.success is False
    assert result.return_code == 1
    assert "failed" in result.stderr.lower()


@pytest.mark.asyncio
async def test_execute_timeout(mock_kubernetes_client):
    """Job 타임아웃 테스트"""
    executor = KubernetesJobExecutor(
        namespace="test-ns",
        poll_interval_seconds=0.1,
        timeout_seconds=0.5,  # 짧은 타임아웃
        in_cluster=False
    )
    executor.validate_environment()

    # Mock Job 생성
    mock_kubernetes_client["batch_v1"].create_namespaced_job.return_value = Mock()

    # Mock Job 상태 (계속 running)
    mock_job_status = Mock()
    mock_job_status.status.succeeded = None
    mock_job_status.status.failed = None
    mock_kubernetes_client["batch_v1"].read_namespaced_job_status.return_value = mock_job_status

    # Mock Job 삭제
    mock_kubernetes_client["batch_v1"].delete_namespaced_job.return_value = Mock()

    # 실행
    result = await executor.execute(
        config_file_path="s3://bucket/config.sumocfg",
        working_directory="/tmp/sumo",
        experiment_id="exp_001",
        variant_id="baseline"
    )

    # 검증
    assert result.success is False
    assert "timeout" in result.stderr.lower()


@pytest.mark.asyncio
async def test_execute_environment_validation_failure():
    """환경 검증 실패 시 실행 테스트"""
    with patch("apps.simulatorrunner.executors.kubernetes_executor.config") as mock_config:
        from kubernetes.config import ConfigException
        mock_config.load_kube_config.side_effect = ConfigException("Config not found")

        executor = KubernetesJobExecutor(in_cluster=False)

        result = await executor.execute(
            config_file_path="s3://bucket/config.sumocfg",
            working_directory="/tmp/sumo"
        )

        assert result.success is False
        assert "config error" in result.stderr.lower()


@pytest.mark.asyncio
async def test_get_pod_logs_no_pods(mock_kubernetes_client):
    """Pod 로그 없음 테스트"""
    executor = KubernetesJobExecutor(in_cluster=False)
    executor.validate_environment()

    # Mock: Pod 없음
    mock_pod_list = Mock()
    mock_pod_list.items = []
    mock_kubernetes_client["core_v1"].list_namespaced_pod.return_value = mock_pod_list

    logs = await executor._get_pod_logs("test-job")

    assert "no pods found" in logs.lower()


@pytest.mark.asyncio
async def test_cleanup_job_already_deleted(mock_kubernetes_client):
    """이미 삭제된 Job cleanup 테스트"""
    from kubernetes.client.rest import ApiException

    executor = KubernetesJobExecutor(in_cluster=False)
    executor.validate_environment()

    # Mock: Job 이미 삭제됨 (404)
    mock_kubernetes_client["batch_v1"].delete_namespaced_job.side_effect = ApiException(status=404)

    # cleanup 호출 (에러 없이 통과해야 함)
    await executor._cleanup_job("test-job")
