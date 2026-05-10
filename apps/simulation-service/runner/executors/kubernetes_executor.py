"""
Kubernetes Job Executor

SUMO Runner를 Kubernetes Job으로 실행
"""

import asyncio
import time
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .executor import SumoExecutor, ExecutionResult


class KubernetesJobExecutor(SumoExecutor):
    """
    Kubernetes Job Executor

    SUMO 시뮬레이션을 Kubernetes Job으로 실행
    """

    def __init__(
        self,
        namespace: str = "agent-t",
        image: str = "simulation-runner:latest",
        image_pull_policy: str = "Always",
        timeout_seconds: int = 600,
        poll_interval_seconds: int = 5,
        storage_gateway_url: str = "http://storage-gateway:9002",
        in_cluster: bool = True,
    ):
        """
        Args:
            namespace: Kubernetes 네임스페이스
            image: SUMO Runner 이미지
            image_pull_policy: 이미지 Pull 정책
            timeout_seconds: Job 실행 타임아웃 (초)
            poll_interval_seconds: Job 상태 폴링 간격 (초)
            storage_gateway_url: StorageGateway URL
            in_cluster: 클러스터 내부에서 실행 여부
        """
        self.namespace = namespace
        self.image = image
        self.image_pull_policy = image_pull_policy
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.storage_gateway_url = storage_gateway_url
        self.in_cluster = in_cluster

        # Kubernetes API 클라이언트
        self.batch_v1: Optional[client.BatchV1Api] = None
        self.core_v1: Optional[client.CoreV1Api] = None

    def validate_environment(self) -> tuple[bool, str]:
        """Kubernetes 환경 검증"""
        try:
            # Kubernetes config 로드
            if self.in_cluster:
                config.load_incluster_config()
            else:
                config.load_kube_config()

            # API 클라이언트 생성
            self.batch_v1 = client.BatchV1Api()
            self.core_v1 = client.CoreV1Api()

            # 네임스페이스 존재 확인
            self.core_v1.read_namespace(name=self.namespace)

            return True, "Kubernetes environment validated"

        except config.ConfigException as e:
            return False, f"Kubernetes config error: {str(e)}"
        except ApiException as e:
            if e.status == 404:
                return False, f"Namespace '{self.namespace}' not found"
            return False, f"Kubernetes API error: {str(e)}"
        except Exception as e:
            return False, f"Environment validation failed: {str(e)}"

    async def execute(
        self,
        config_file_path: str,
        working_directory: str,
        experiment_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        variant_id: Optional[str] = None,
        network_artifact_uri: Optional[str] = None,
        demand_artifact_uri: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Kubernetes Job으로 SUMO 실행

        Args:
            config_file_path: SUMO config 파일 경로 (S3 URI)
            working_directory: 작업 디렉토리 (사용하지 않음, Job 내부에서 생성)
            experiment_id: 실험 ID
            scenario_id: 시나리오 ID
            variant_id: 변형 ID
            network_artifact_uri: 네트워크 파일 URI
            demand_artifact_uri: 수요 파일 URI

        Returns:
            ExecutionResult
        """
        start_time = time.time()

        # 환경 검증
        is_valid, message = self.validate_environment()
        if not is_valid:
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=message,
                execution_time_seconds=0.0,
                output_files={}
            )

        # Job 이름 생성 (Kubernetes DNS 호환)
        job_name = self._generate_job_name(experiment_id, variant_id)

        try:
            # Job manifest 생성
            job_manifest = self._create_job_manifest(
                job_name=job_name,
                config_file_uri=config_file_path,
                experiment_id=experiment_id,
                scenario_id=scenario_id,
                variant_id=variant_id,
                network_artifact_uri=network_artifact_uri,
                demand_artifact_uri=demand_artifact_uri,
            )

            # Job 생성
            self.batch_v1.create_namespaced_job(
                namespace=self.namespace,
                body=job_manifest
            )

            # Job 상태 폴링
            success, stdout, stderr, output_files = await self._wait_for_job_completion(
                job_name=job_name
            )

            execution_time = time.time() - start_time

            # Job 삭제 (cleanup)
            await self._cleanup_job(job_name)

            return ExecutionResult(
                success=success,
                return_code=0 if success else 1,
                stdout=stdout,
                stderr=stderr,
                execution_time_seconds=execution_time,
                output_files=output_files
            )

        except ApiException as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Kubernetes API error: {e.status} - {e.reason}",
                execution_time_seconds=execution_time,
                output_files={}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Job execution failed: {str(e)}",
                execution_time_seconds=execution_time,
                output_files={}
            )

    def _generate_job_name(self, experiment_id: Optional[str], variant_id: Optional[str]) -> str:
        """
        Kubernetes Job 이름 생성

        DNS-1123 호환 (소문자, 숫자, 하이픈만 허용, 63자 제한)
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]

        parts = ["sumo", "sim"]

        if experiment_id:
            # experiment_id에서 영숫자만 추출
            clean_exp_id = "".join(c for c in experiment_id if c.isalnum()).lower()[:10]
            if clean_exp_id:
                parts.append(clean_exp_id)

        if variant_id:
            clean_variant_id = "".join(c for c in variant_id if c.isalnum()).lower()[:8]
            if clean_variant_id:
                parts.append(clean_variant_id)

        parts.append(timestamp)
        parts.append(unique_id)

        job_name = "-".join(parts)

        # 63자 제한
        if len(job_name) > 63:
            job_name = job_name[:63]

        return job_name

    def _create_job_manifest(
        self,
        job_name: str,
        config_file_uri: str,
        experiment_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        variant_id: Optional[str] = None,
        network_artifact_uri: Optional[str] = None,
        demand_artifact_uri: Optional[str] = None,
    ) -> client.V1Job:
        """
        Kubernetes Job manifest 생성

        Args:
            job_name: Job 이름
            config_file_uri: SUMO config 파일 URI (S3)
            experiment_id: 실험 ID
            scenario_id: 시나리오 ID
            variant_id: 변형 ID
            network_artifact_uri: 네트워크 파일 URI
            demand_artifact_uri: 수요 파일 URI

        Returns:
            V1Job manifest
        """
        # 환경변수
        env_vars = [
            client.V1EnvVar(name="CONFIG_FILE_URI", value=config_file_uri),
            client.V1EnvVar(name="STORAGE_GATEWAY_URL", value=self.storage_gateway_url),
            client.V1EnvVar(name="SUMO_BINARY", value="sumo"),
        ]

        if experiment_id:
            env_vars.append(client.V1EnvVar(name="EXPERIMENT_ID", value=experiment_id))
        if scenario_id:
            env_vars.append(client.V1EnvVar(name="SCENARIO_ID", value=scenario_id))
        if variant_id:
            env_vars.append(client.V1EnvVar(name="VARIANT_ID", value=variant_id))
        if network_artifact_uri:
            env_vars.append(client.V1EnvVar(name="NETWORK_ARTIFACT_URI", value=network_artifact_uri))
        if demand_artifact_uri:
            env_vars.append(client.V1EnvVar(name="DEMAND_ARTIFACT_URI", value=demand_artifact_uri))

        # Container
        container = client.V1Container(
            name="sumo-runner",
            image=self.image,
            image_pull_policy=self.image_pull_policy,
            env=env_vars,
            resources=client.V1ResourceRequirements(
                requests={"cpu": "500m", "memory": "1Gi"},
                limits={"cpu": "2000m", "memory": "4Gi"}
            ),
        )

        # Pod template
        pod_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={
                    "app": "sumo-runner",
                    "job-name": job_name,
                    "experiment-id": experiment_id or "unknown",
                    "variant-id": variant_id or "unknown",
                }
            ),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[container],
                service_account_name="sumo-runner",
            )
        )

        # Job spec
        job_spec = client.V1JobSpec(
            template=pod_template,
            backoff_limit=0,  # 재시도 없음
            ttl_seconds_after_finished=3600,  # 완료 후 1시간 뒤 자동 삭제
        )

        # Job
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                labels={
                    "app": "sumo-runner",
                    "experiment-id": experiment_id or "unknown",
                    "variant-id": variant_id or "unknown",
                }
            ),
            spec=job_spec
        )

        return job

    async def _wait_for_job_completion(
        self,
        job_name: str
    ) -> tuple[bool, str, str, Dict[str, str]]:
        """
        Job 완료 대기 (polling)

        Args:
            job_name: Job 이름

        Returns:
            (success, stdout, stderr, output_files)
        """
        start_time = time.time()
        stdout_lines = []
        stderr_lines = []

        while True:
            # 타임아웃 체크
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                stderr_lines.append(f"Job timeout after {self.timeout_seconds} seconds")
                return False, "\n".join(stdout_lines), "\n".join(stderr_lines), {}

            # Job 상태 조회
            try:
                job = self.batch_v1.read_namespaced_job_status(
                    name=job_name,
                    namespace=self.namespace
                )

                # Job 상태 확인
                if job.status.succeeded:
                    # 성공
                    stdout_lines.append(f"Job {job_name} completed successfully")
                    # Pod 로그 수집
                    logs = await self._get_pod_logs(job_name)
                    stdout_lines.append(logs)
                    return True, "\n".join(stdout_lines), "\n".join(stderr_lines), {}

                elif job.status.failed:
                    # 실패
                    stderr_lines.append(f"Job {job_name} failed")
                    # Pod 로그 수집
                    logs = await self._get_pod_logs(job_name)
                    stderr_lines.append(logs)
                    return False, "\n".join(stdout_lines), "\n".join(stderr_lines), {}

                # 진행 중
                stdout_lines.append(f"Job {job_name} is running... (elapsed: {elapsed:.1f}s)")

            except ApiException as e:
                stderr_lines.append(f"Failed to check job status: {e.status} - {e.reason}")
                return False, "\n".join(stdout_lines), "\n".join(stderr_lines), {}

            # 대기
            await asyncio.sleep(self.poll_interval_seconds)

    async def _get_pod_logs(self, job_name: str) -> str:
        """
        Job의 Pod 로그 수집

        Args:
            job_name: Job 이름

        Returns:
            Pod 로그
        """
        try:
            # Job의 Pod 찾기
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"job-name={job_name}"
            )

            if not pods.items:
                return "No pods found for job"

            # 첫 번째 Pod의 로그 가져오기
            pod_name = pods.items[0].metadata.name
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                container="sumo-runner"
            )

            return logs

        except ApiException as e:
            return f"Failed to retrieve pod logs: {e.status} - {e.reason}"
        except Exception as e:
            return f"Failed to retrieve pod logs: {str(e)}"

    async def _cleanup_job(self, job_name: str):
        """
        Job 삭제 (cleanup)

        Args:
            job_name: Job 이름
        """
        try:
            # Job 삭제 (propagation_policy="Background"로 Pod도 함께 삭제)
            self.batch_v1.delete_namespaced_job(
                name=job_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(propagation_policy="Background")
            )
        except ApiException as e:
            # 이미 삭제된 경우 무시
            if e.status != 404:
                print(f"Warning: Failed to delete job {job_name}: {e.status} - {e.reason}")
        except Exception as e:
            print(f"Warning: Failed to delete job {job_name}: {str(e)}")
