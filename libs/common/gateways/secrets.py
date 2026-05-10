"""
Secret/Config Provider
비밀 및 설정 관리 추상화 계층
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import json


class SecretConfigProvider(ABC):
    """
    Secret/Config Provider Base Class

    비밀(credentials, API keys 등) 및 설정 관리
    AWS Secrets Manager, HashiCorp Vault 등
    """

    @abstractmethod
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        비밀 조회

        Args:
            secret_name: 비밀 이름

        Returns:
            Dict[str, Any]: 비밀 내용 (JSON 파싱)
        """
        pass

    @abstractmethod
    async def get_config(self, config_name: str) -> Dict[str, Any]:
        """
        설정 조회

        Args:
            config_name: 설정 이름

        Returns:
            Dict[str, Any]: 설정 내용
        """
        pass

    @abstractmethod
    async def set_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        비밀 저장

        Args:
            secret_name: 비밀 이름
            secret_value: 비밀 내용

        Returns:
            bool: 성공 여부
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 이름"""
        pass


# ============================================================================
# Environment Variable Provider
# ============================================================================

class EnvVarProvider(SecretConfigProvider):
    """
    Environment Variable Provider

    환경 변수에서 비밀/설정 조회
    개발 환경용
    """

    def __init__(self, **kwargs):
        self.prefix = kwargs.get("prefix", "")

    @property
    def provider_name(self) -> str:
        return "env"

    def _get_key(self, name: str) -> str:
        """환경 변수 키 생성"""
        if self.prefix:
            return f"{self.prefix}_{name}".upper()
        return name.upper()

    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """환경 변수에서 비밀 조회"""
        key = self._get_key(secret_name)
        value = os.getenv(key)

        if value is None:
            raise ValueError(f"Secret not found: {key}")

        # JSON으로 파싱 시도
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # 단순 문자열이면 딕셔너리로 감싸기
            return {"value": value}

    async def get_config(self, config_name: str) -> Dict[str, Any]:
        """설정 조회 (비밀과 동일)"""
        return await self.get_secret(config_name)

    async def set_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """환경 변수 설정 (런타임에는 불가)"""
        # 환경 변수는 프로세스 시작 시 설정되므로 런타임 변경 불가
        return False


# ============================================================================
# AWS Secrets Manager Provider
# ============================================================================

class AWSSecretsManagerProvider(SecretConfigProvider):
    """
    AWS Secrets Manager Provider

    AWS Secrets Manager에서 비밀 조회
    """

    def __init__(self, region: Optional[str] = None, **kwargs):
        self.region = region or os.getenv("AWS_REGION", "ap-northeast-2")
        self._client = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    @property
    def provider_name(self) -> str:
        return "aws_secrets_manager"

    def _get_client(self):
        """Boto3 클라이언트 lazy 초기화"""
        if self._client is None:
            import boto3
            self._client = boto3.client("secretsmanager", region_name=self.region)
        return self._client

    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Secrets Manager에서 비밀 조회"""
        # 캐시 확인
        if secret_name in self._cache:
            return self._cache[secret_name]

        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)

            # JSON 파싱
            if "SecretString" in response:
                secret = json.loads(response["SecretString"])
            else:
                # Binary secret
                import base64
                secret = {"binary": base64.b64encode(response["SecretBinary"]).decode()}

            # 캐시 저장
            self._cache[secret_name] = secret
            return secret

        except Exception as e:
            raise ValueError(f"Failed to get secret '{secret_name}': {str(e)}")

    async def get_config(self, config_name: str) -> Dict[str, Any]:
        """설정 조회 (비밀과 동일)"""
        return await self.get_secret(config_name)

    async def set_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """비밀 저장/업데이트"""
        try:
            client = self._get_client()
            secret_string = json.dumps(secret_value)

            try:
                # 업데이트 시도
                client.update_secret(
                    SecretId=secret_name,
                    SecretString=secret_string,
                )
            except client.exceptions.ResourceNotFoundException:
                # 없으면 생성
                client.create_secret(
                    Name=secret_name,
                    SecretString=secret_string,
                )

            # 캐시 업데이트
            self._cache[secret_name] = secret_value
            return True

        except Exception:
            return False


# ============================================================================
# File-based Provider
# ============================================================================

class FileBasedProvider(SecretConfigProvider):
    """
    File-based Provider

    로컬 파일에서 비밀/설정 조회
    개발 및 테스트용
    """

    def __init__(self, secrets_dir: str = "./secrets", **kwargs):
        from pathlib import Path
        self.secrets_dir = Path(secrets_dir)
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

    @property
    def provider_name(self) -> str:
        return "file"

    def _get_file_path(self, name: str) -> "Path":
        """파일 경로 생성"""
        return self.secrets_dir / f"{name}.json"

    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """파일에서 비밀 조회"""
        file_path = self._get_file_path(secret_name)

        if not file_path.exists():
            raise ValueError(f"Secret file not found: {file_path}")

        try:
            content = file_path.read_text()
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Failed to read secret '{secret_name}': {str(e)}")

    async def get_config(self, config_name: str) -> Dict[str, Any]:
        """설정 조회"""
        return await self.get_secret(config_name)

    async def set_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """비밀 저장"""
        file_path = self._get_file_path(secret_name)

        try:
            content = json.dumps(secret_value, indent=2)
            file_path.write_text(content)
            return True
        except Exception:
            return False


# ============================================================================
# Factory Function
# ============================================================================

def get_secret_provider(
    provider: Optional[str] = None,
    **kwargs
) -> SecretConfigProvider:
    """
    Secret Config Provider Factory

    환경 변수:
        SECRET_PROVIDER: env | aws | file (기본: env)
        AWS_REGION: AWS 리전 (aws)
        SECRETS_DIR: 비밀 디렉토리 (file)

    Args:
        provider: Provider 이름
        **kwargs: 추가 설정

    Returns:
        SecretConfigProvider: 선택된 Provider

    Example:
        >>> secrets = get_secret_provider()
        >>> db_creds = await secrets.get_secret("database/credentials")
        >>> print(db_creds["username"])
    """
    provider = provider or os.getenv("SECRET_PROVIDER", "env")
    provider = provider.lower()

    if provider == "env":
        return EnvVarProvider(**kwargs)

    elif provider == "aws":
        return AWSSecretsManagerProvider(**kwargs)

    elif provider == "file":
        secrets_dir = kwargs.get("secrets_dir") or os.getenv("SECRETS_DIR", "./secrets")
        return FileBasedProvider(secrets_dir=secrets_dir, **kwargs)

    else:
        raise ValueError(f"Unknown secret provider: {provider}")
