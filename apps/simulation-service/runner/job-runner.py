"""
SUMO Job Runner

Kubernetes Job 내부에서 실행되는 스크립트
환경변수로 전달된 artifact URI를 다운로드하고 SUMO 실행 후 결과 업로드
"""

import os
import sys
import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Optional

# StorageGateway 클라이언트 (HTTP)
import httpx


async def download_artifact(storage_gateway_url: str, artifact_uri: str, local_path: str) -> bool:
    """
    StorageGateway를 통해 artifact 다운로드

    Args:
        storage_gateway_url: StorageGateway URL
        artifact_uri: 아티팩트 URI (S3 등)
        local_path: 로컬 저장 경로

    Returns:
        성공 여부
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{storage_gateway_url}/download",
                json={"uri": artifact_uri}
            )

            if response.status_code != 200:
                print(f"Failed to download {artifact_uri}: {response.status_code}")
                return False

            # 파일 저장
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(response.content)

            print(f"Downloaded {artifact_uri} to {local_path}")
            return True

    except Exception as e:
        print(f"Download error: {str(e)}")
        return False


async def upload_artifact(storage_gateway_url: str, local_path: str, remote_uri: str) -> bool:
    """
    StorageGateway를 통해 artifact 업로드

    Args:
        storage_gateway_url: StorageGateway URL
        local_path: 로컬 파일 경로
        remote_uri: 원격 URI (S3 등)

    Returns:
        성공 여부
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(local_path, "rb") as f:
                files = {"file": f}
                data = {"uri": remote_uri}
                response = await client.post(
                    f"{storage_gateway_url}/upload",
                    data=data,
                    files=files
                )

            if response.status_code != 200:
                print(f"Failed to upload {local_path} to {remote_uri}: {response.status_code}")
                return False

            print(f"Uploaded {local_path} to {remote_uri}")
            return True

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return False


async def run_sumo(
    sumo_binary: str,
    config_file_path: str,
    working_dir: str,
    timeout_seconds: int = 600
) -> tuple[bool, str, str]:
    """
    SUMO 실행

    Args:
        sumo_binary: SUMO 바이너리 경로
        config_file_path: config 파일 경로
        working_dir: 작업 디렉토리
        timeout_seconds: 타임아웃 (초)

    Returns:
        (success, stdout, stderr)
    """
    command = [sumo_binary, "-c", config_file_path]

    try:
        print(f"Running SUMO: {' '.join(command)}")
        print(f"Working directory: {working_dir}")

        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 타임아웃과 함께 대기
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds
        )

        stdout_str = stdout.decode("utf-8") if stdout else ""
        stderr_str = stderr.decode("utf-8") if stderr else ""

        success = process.returncode == 0

        if success:
            print("SUMO completed successfully")
        else:
            print(f"SUMO failed with return code {process.returncode}")

        return success, stdout_str, stderr_str

    except asyncio.TimeoutError:
        print(f"SUMO timeout after {timeout_seconds} seconds")
        process.kill()
        return False, "", f"SUMO timeout after {timeout_seconds} seconds"

    except Exception as e:
        print(f"SUMO execution error: {str(e)}")
        return False, "", str(e)


async def main():
    """메인 실행 로직"""

    # 환경변수 읽기
    config_file_uri = os.getenv("CONFIG_FILE_URI")
    storage_gateway_url = os.getenv("STORAGE_GATEWAY_URL", "http://storage-gateway:9002")
    sumo_binary = os.getenv("SUMO_BINARY", "sumo")
    experiment_id = os.getenv("EXPERIMENT_ID", "unknown")
    scenario_id = os.getenv("SCENARIO_ID", "unknown")
    variant_id = os.getenv("VARIANT_ID", "unknown")
    network_artifact_uri = os.getenv("NETWORK_ARTIFACT_URI")
    demand_artifact_uri = os.getenv("DEMAND_ARTIFACT_URI")

    print("=" * 80)
    print("SUMO Job Runner")
    print("=" * 80)
    print(f"Experiment ID: {experiment_id}")
    print(f"Scenario ID: {scenario_id}")
    print(f"Variant ID: {variant_id}")
    print(f"Config URI: {config_file_uri}")
    print(f"Network URI: {network_artifact_uri}")
    print(f"Demand URI: {demand_artifact_uri}")
    print(f"Storage Gateway: {storage_gateway_url}")
    print(f"SUMO Binary: {sumo_binary}")
    print("=" * 80)

    # 필수 환경변수 확인
    if not config_file_uri:
        print("ERROR: CONFIG_FILE_URI is required")
        sys.exit(1)

    # 작업 디렉토리 생성
    working_dir = Path("/tmp/sumo_job")
    working_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Config 파일 다운로드
        print("\n[1/5] Downloading config file...")
        config_local_path = working_dir / "simulation.sumocfg"
        if not await download_artifact(storage_gateway_url, config_file_uri, str(config_local_path)):
            print("ERROR: Failed to download config file")
            sys.exit(1)

        # 2. Network 파일 다운로드 (선택)
        if network_artifact_uri:
            print("\n[2/5] Downloading network file...")
            network_local_path = working_dir / "network.net.xml"
            if not await download_artifact(storage_gateway_url, network_artifact_uri, str(network_local_path)):
                print("ERROR: Failed to download network file")
                sys.exit(1)

        # 3. Demand 파일 다운로드 (선택)
        if demand_artifact_uri:
            print("\n[3/5] Downloading demand file...")
            demand_local_path = working_dir / "demand.rou.xml"
            if not await download_artifact(storage_gateway_url, demand_artifact_uri, str(demand_local_path)):
                print("ERROR: Failed to download demand file")
                sys.exit(1)

        # 4. SUMO 실행
        print("\n[4/5] Running SUMO simulation...")
        success, stdout, stderr = await run_sumo(
            sumo_binary=sumo_binary,
            config_file_path=str(config_local_path),
            working_dir=str(working_dir),
            timeout_seconds=600
        )

        if not success:
            print("ERROR: SUMO simulation failed")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            sys.exit(1)

        # 5. 결과 파일 업로드
        print("\n[5/5] Uploading result files...")

        output_files = {
            "tripinfo.xml": f"s3://sumo-results/{experiment_id}/{variant_id}/tripinfo.xml",
            "summary.xml": f"s3://sumo-results/{experiment_id}/{variant_id}/summary.xml",
            "queue.xml": f"s3://sumo-results/{experiment_id}/{variant_id}/queue.xml",
            "emission.xml": f"s3://sumo-results/{experiment_id}/{variant_id}/emission.xml",
        }

        upload_success = True
        for filename, remote_uri in output_files.items():
            local_file = working_dir / filename
            if local_file.exists():
                if not await upload_artifact(storage_gateway_url, str(local_file), remote_uri):
                    print(f"WARNING: Failed to upload {filename}")
                    upload_success = False
            else:
                print(f"WARNING: Output file {filename} not found")

        if not upload_success:
            print("ERROR: Some files failed to upload")
            sys.exit(1)

        print("\n" + "=" * 80)
        print("SUMO Job completed successfully")
        print("=" * 80)
        sys.exit(0)

    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
