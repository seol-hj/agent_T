"""
Storage Gateway
스토리지 Provider 추상화 계층
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Dict, Any, List
import os
from pathlib import Path
import shutil
from io import BytesIO


class StorageGateway(ABC):
    """
    Storage Gateway Base Class

    모든 Storage Provider는 이 인터페이스를 구현한다.
    S3, MinIO, 로컬 파일시스템 등을 동일한 인터페이스로 접근
    """

    @abstractmethod
    async def upload(
        self,
        file_path: str,
        content: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        파일 업로드

        Args:
            file_path: 저장 경로 (예: "scenarios/exp-001/scenario.json")
            content: 파일 내용 (bytes)
            content_type: MIME type
            metadata: 메타데이터

        Returns:
            str: 저장된 파일 URI
        """
        pass

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        """
        파일 다운로드

        Args:
            file_path: 파일 경로

        Returns:
            bytes: 파일 내용
        """
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """
        파일 삭제

        Args:
            file_path: 파일 경로

        Returns:
            bool: 성공 여부
        """
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """
        파일 존재 확인

        Args:
            file_path: 파일 경로

        Returns:
            bool: 존재 여부
        """
        pass

    @abstractmethod
    async def list(self, prefix: str = "") -> List[str]:
        """
        파일 목록 조회

        Args:
            prefix: 경로 prefix

        Returns:
            List[str]: 파일 경로 목록
        """
        pass

    @abstractmethod
    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Presigned URL 생성

        Args:
            file_path: 파일 경로
            expires_in: 만료 시간 (초)

        Returns:
            str: Presigned URL
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 이름"""
        pass


# ============================================================================
# Local Storage Provider
# ============================================================================

class LocalStorageGateway(StorageGateway):
    """
    Local File System Provider

    로컬 파일시스템을 Storage Gateway로 사용
    개발 환경용
    """

    def __init__(self, base_path: str = "./data", **kwargs):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    @property
    def provider_name(self) -> str:
        return "local"

    def _get_full_path(self, file_path: str) -> Path:
        """전체 경로 생성"""
        return self.base_path / file_path

    async def upload(
        self,
        file_path: str,
        content: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """로컬 파일 저장"""
        full_path = self._get_full_path(file_path)

        # 디렉토리 생성 (권한 에러 처리)
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True, mode=0o777)
        except PermissionError:
            # 권한 문제가 있을 경우 임시 디렉토리 사용
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "agent-t-storage"
            temp_dir.mkdir(parents=True, exist_ok=True)
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

        full_path.write_bytes(content)

        # 메타데이터는 별도 파일로 저장
        if metadata:
            meta_path = full_path.with_suffix(full_path.suffix + ".meta")
            import json
            meta_path.write_text(json.dumps(metadata))

        return f"file://{full_path}"

    async def download(self, file_path: str) -> bytes:
        """로컬 파일 읽기"""
        # file:// URI인 경우 절대 경로로 변환
        if file_path.startswith("file://"):
            full_path = Path(file_path.replace("file://", ""))
        else:
            full_path = self._get_full_path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return full_path.read_bytes()

    async def delete(self, file_path: str) -> bool:
        """로컬 파일 삭제"""
        # file:// URI인 경우 절대 경로로 변환
        if file_path.startswith("file://"):
            full_path = Path(file_path.replace("file://", ""))
        else:
            full_path = self._get_full_path(file_path)

        if not full_path.exists():
            return False

        full_path.unlink()

        # 메타데이터 파일도 삭제
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")
        if meta_path.exists():
            meta_path.unlink()

        return True

    async def exists(self, file_path: str) -> bool:
        """파일 존재 확인"""
        # file:// URI인 경우 절대 경로로 변환
        if file_path.startswith("file://"):
            full_path = Path(file_path.replace("file://", ""))
        else:
            full_path = self._get_full_path(file_path)
        return full_path.exists()

    async def list(self, prefix: str = "") -> List[str]:
        """파일 목록"""
        search_path = self._get_full_path(prefix)

        if not search_path.exists():
            return []

        files = []
        if search_path.is_dir():
            for file in search_path.rglob("*"):
                if file.is_file() and not file.suffix == ".meta":
                    rel_path = file.relative_to(self.base_path)
                    files.append(str(rel_path))
        else:
            if search_path.is_file():
                rel_path = search_path.relative_to(self.base_path)
                files.append(str(rel_path))

        return sorted(files)

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """로컬 파일 URL"""
        full_path = self._get_full_path(file_path)
        return f"file://{full_path.absolute()}"


# ============================================================================
# S3 Storage Provider
# ============================================================================

class S3StorageGateway(StorageGateway):
    """
    Amazon S3 Provider

    S3 버킷을 Storage Gateway로 사용
    """

    def __init__(self, bucket_name: str, **kwargs):
        self.bucket_name = bucket_name
        self.region = kwargs.get("region", os.getenv("AWS_REGION", "ap-northeast-2"))
        self.prefix = kwargs.get("prefix", "")
        self._client = None

    @property
    def provider_name(self) -> str:
        return "s3"

    def _get_client(self):
        """Boto3 클라이언트 lazy 초기화"""
        if self._client is None:
            import boto3
            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    def _get_key(self, file_path: str) -> str:
        """S3 키 생성"""
        if self.prefix:
            return f"{self.prefix}/{file_path}"
        return file_path

    async def upload(
        self,
        file_path: str,
        content: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """S3 업로드"""
        client = self._get_client()
        key = self._get_key(file_path)

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata

        client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            **extra_args
        )

        return f"s3://{self.bucket_name}/{key}"

    async def download(self, file_path: str) -> bytes:
        """S3 다운로드"""
        client = self._get_client()
        key = self._get_key(file_path)

        try:
            response = client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"File not found: s3://{self.bucket_name}/{key}")

    async def delete(self, file_path: str) -> bool:
        """S3 삭제"""
        client = self._get_client()
        key = self._get_key(file_path)

        try:
            client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    async def exists(self, file_path: str) -> bool:
        """S3 파일 존재 확인"""
        client = self._get_client()
        key = self._get_key(file_path)

        try:
            client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except:
            return False

    async def list(self, prefix: str = "") -> List[str]:
        """S3 파일 목록"""
        client = self._get_client()
        search_prefix = self._get_key(prefix)

        files = []
        paginator = client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=search_prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    # prefix 제거
                    if self.prefix and key.startswith(self.prefix + "/"):
                        key = key[len(self.prefix) + 1:]
                    files.append(key)

        return sorted(files)

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """S3 Presigned URL"""
        client = self._get_client()
        key = self._get_key(file_path)

        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )

        return url


# ============================================================================
# MinIO Provider (Placeholder)
# ============================================================================

class MinIOStorageProvider(StorageGateway):
    """
    MinIO Provider (Placeholder)

    Self-hosted S3 호환 스토리지
    향후 구현
    """

    def __init__(self, endpoint: str, bucket_name: str, **kwargs):
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.access_key = kwargs.get("access_key")
        self.secret_key = kwargs.get("secret_key")

    @property
    def provider_name(self) -> str:
        return "minio"

    async def upload(self, file_path: str, content: bytes, **kwargs) -> str:
        raise NotImplementedError("MinIOStorageProvider is not implemented yet")

    async def download(self, file_path: str) -> bytes:
        raise NotImplementedError("MinIOStorageProvider is not implemented yet")

    async def delete(self, file_path: str) -> bool:
        raise NotImplementedError("MinIOStorageProvider is not implemented yet")

    async def exists(self, file_path: str) -> bool:
        raise NotImplementedError("MinIOStorageProvider is not implemented yet")

    async def list(self, prefix: str = "") -> List[str]:
        raise NotImplementedError("MinIOStorageProvider is not implemented yet")

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        raise NotImplementedError("MinIOStorageProvider is not implemented yet")


# ============================================================================
# Factory Function
# ============================================================================

def get_storage_gateway(
    provider: Optional[str] = None,
    bucket_name: Optional[str] = None,
    **kwargs
) -> StorageGateway:
    """
    Storage Gateway Factory

    환경 변수:
        STORAGE_PROVIDER: local | s3 | minio (기본: local)
        STORAGE_BUCKET: 버킷 이름 (S3/MinIO)
        STORAGE_BASE_PATH: 로컬 저장 경로 (local)

    Args:
        provider: Provider 이름
        bucket_name: 버킷 이름 (S3/MinIO)
        **kwargs: 추가 설정

    Returns:
        StorageGateway: 선택된 Provider

    Example:
        >>> storage = get_storage_gateway()
        >>> await storage.upload("file.txt", b"content")
    """
    provider = provider or os.getenv("STORAGE_PROVIDER", "local")
    provider = provider.lower()

    if provider == "local":
        base_path = kwargs.get("base_path") or os.getenv("STORAGE_BASE_PATH", "./data")
        return LocalStorageGateway(base_path=base_path, **kwargs)

    elif provider == "s3":
        bucket_name = bucket_name or os.getenv("STORAGE_BUCKET")
        if not bucket_name:
            raise ValueError("S3 bucket_name is required")
        return S3StorageGateway(bucket_name=bucket_name, **kwargs)

    elif provider == "minio":
        endpoint = kwargs.get("endpoint") or os.getenv("MINIO_ENDPOINT")
        bucket_name = bucket_name or os.getenv("STORAGE_BUCKET")
        if not endpoint or not bucket_name:
            raise ValueError("MinIO endpoint and bucket_name are required")
        return MinIOStorageProvider(endpoint=endpoint, bucket_name=bucket_name, **kwargs)

    else:
        raise ValueError(f"Unknown storage provider: {provider}")
