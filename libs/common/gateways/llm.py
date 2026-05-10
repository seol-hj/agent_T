"""
LLM Gateway
LLM Provider 추상화 계층
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
import time
from ..models.llm_response import LLMResponse, LLMUsageMetadata


class LLMGateway(ABC):
    """
    LLM Gateway Base Class

    모든 LLM Provider는 이 인터페이스를 구현한다.
    직접 Bedrock/OpenAI SDK를 호출하지 않고 반드시 Gateway를 거친다.
    """

    def __init__(self, model_id: str, **kwargs):
        self.model_id = model_id
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0 ~ 1.0)
            prompt_version: 프롬프트 버전 (추적용)
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 생성 결과 및 메타데이터
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ):
        """
        스트리밍 생성

        Args:
            동일

        Yields:
            str: 생성된 텍스트 청크
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        채팅 (대화 이력 포함)

        Args:
            messages: 대화 이력 [{"role": "user", "content": "..."}]
            max_tokens: 최대 토큰 수
            temperature: 온도
            prompt_version: 프롬프트 버전
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 응답 및 메타데이터
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 이름"""
        pass


# ============================================================================
# Mock Provider (테스트용)
# ============================================================================

class MockLLMProvider(LLMGateway):
    """
    Mock LLM Provider

    테스트 및 개발 환경용
    실제 LLM API를 호출하지 않고 더미 응답 반환
    """

    def __init__(self, model_id: str = "mock-model-v1", **kwargs):
        super().__init__(model_id, **kwargs)
        self.delay_ms = kwargs.get("delay_ms", 100)

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Mock 응답 생성"""
        start_time = time.time()

        # 인위적 지연
        await self._simulate_delay()

        # Mock 응답
        content = f"[Mock Response] Received prompt: '{prompt[:50]}...'"
        if system_prompt:
            content += f"\n[System]: {system_prompt[:30]}..."

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=content,
            model_id=self.model_id,
            provider=self.provider_name,
            prompt_version=prompt_version or "unknown",
            latency_ms=latency_ms,
            usage=LLMUsageMetadata(
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(content.split()),
                total_tokens=len(prompt.split()) + len(content.split()),
            ),
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ):
        """Mock 스트리밍"""
        chunks = ["Mock ", "streaming ", "response ", "here"]
        for chunk in chunks:
            await self._simulate_delay()
            yield chunk

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Mock 채팅"""
        last_message = messages[-1]["content"] if messages else ""
        return await self.generate(
            prompt=last_message,
            system_prompt=f"Chat with {len(messages)} message(s)",
            max_tokens=max_tokens,
            temperature=temperature,
            prompt_version=prompt_version,
            **kwargs
        )

    async def _simulate_delay(self):
        """지연 시뮬레이션"""
        import asyncio
        await asyncio.sleep(self.delay_ms / 1000.0)


# ============================================================================
# Bedrock Provider
# ============================================================================

class BedrockLLMGateway(LLMGateway):
    """
    Amazon Bedrock Provider

    AWS Bedrock을 통해 Claude 3, Titan 등의 모델 호출

    Features:
    - IAM Role/IRSA 기반 인증 (credentials 하드코딩 금지)
    - Retry with exponential backoff
    - Timeout 설정
    - 상세한 에러 메시지
    - Structured output 지원

    환경 변수:
        AWS_REGION: AWS 리전 (기본: ap-northeast-2)
        BEDROCK_MODEL_ID: 모델 ID (기본: claude-3-sonnet)
        BEDROCK_TIMEOUT: 타임아웃 초 (기본: 60)
        BEDROCK_MAX_RETRIES: 최대 재시도 (기본: 3)
    """

    def __init__(self, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0", **kwargs):
        super().__init__(model_id, **kwargs)

        # AWS 설정 (환경변수 우선)
        self.region = kwargs.get("region") or os.getenv("AWS_REGION", "ap-northeast-2")

        # Timeout/Retry 설정
        self.timeout = int(kwargs.get("timeout") or os.getenv("BEDROCK_TIMEOUT", "60"))
        self.max_retries = int(kwargs.get("max_retries") or os.getenv("BEDROCK_MAX_RETRIES", "3"))

        # 클라이언트 (lazy initialization)
        self._client = None
        self._mock_mode = kwargs.get("mock_mode", False)

    @property
    def provider_name(self) -> str:
        return "bedrock"

    def _get_client(self):
        """
        Boto3 클라이언트 lazy 초기화

        IAM Role/IRSA 환경에서 자동으로 credentials 획득
        명시적 credentials 하드코딩 금지
        """
        if self._client is None:
            import boto3
            from botocore.config import Config

            # Mock 모드
            if self._mock_mode:
                return None

            # Boto3 Config (timeout, retry)
            config = Config(
                region_name=self.region,
                connect_timeout=self.timeout,
                read_timeout=self.timeout,
                retries={
                    "max_attempts": self.max_retries,
                    "mode": "adaptive",  # adaptive retry mode
                }
            )

            # IAM Role/IRSA 기반 자동 인증
            # credentials 명시 X → boto3가 자동으로 찾음:
            # 1. 환경변수 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # 2. ~/.aws/credentials
            # 3. IAM Instance Profile (EC2)
            # 4. Web Identity Token (EKS IRSA)
            self._client = boto3.client(
                "bedrock-runtime",
                config=config
            )

        return self._client

    def _parse_bedrock_error(self, error: Exception) -> str:
        """
        Bedrock 에러를 명확한 메시지로 변환

        Args:
            error: 원본 예외

        Returns:
            str: 사용자 친화적 에러 메시지
        """
        error_str = str(error)
        error_type = type(error).__name__

        # 일반적인 Bedrock 에러 패턴
        if "ValidationException" in error_type:
            return f"Bedrock 검증 오류: {error_str} (모델 ID 또는 요청 파라미터 확인)"

        elif "ThrottlingException" in error_type:
            return f"Bedrock 요청 제한 초과: {error_str} (잠시 후 재시도)"

        elif "ModelTimeoutException" in error_type:
            return f"Bedrock 모델 타임아웃: {error_str} (요청이 너무 오래 걸림)"

        elif "AccessDeniedException" in error_type:
            return f"Bedrock 접근 권한 없음: {error_str} (IAM 권한 확인 필요)"

        elif "ResourceNotFoundException" in error_type:
            return f"Bedrock 모델 없음: {error_str} (model_id 확인: {self.model_id})"

        elif "ServiceUnavailableException" in error_type:
            return f"Bedrock 서비스 일시적 불가: {error_str} (잠시 후 재시도)"

        elif "ModelNotReadyException" in error_type:
            return f"Bedrock 모델 준비 중: {error_str} (모델이 아직 로드되지 않음)"

        elif "NoCredentialsError" in error_type or "CredentialsError" in error_type:
            return f"AWS 인증 실패: {error_str} (IAM Role/IRSA 설정 확인)"

        elif "EndpointConnectionError" in error_type or "ConnectTimeout" in error_type:
            return f"Bedrock 연결 실패: {error_str} (네트워크 또는 리전 확인: {self.region})"

        else:
            return f"Bedrock 호출 실패 ({error_type}): {error_str}"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0 ~ 1.0)
            prompt_version: 프롬프트 버전 (추적용)
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 생성 결과 및 메타데이터
        """
        import json
        start_time = time.time()

        try:
            client = self._get_client()

            # Mock 모드
            if self._mock_mode:
                return await self._generate_mock(prompt, system_prompt, max_tokens, temperature, prompt_version)

            # Claude 3 메시지 포맷
            messages = [{"role": "user", "content": prompt}]

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            if system_prompt:
                body["system"] = system_prompt

            # 추가 파라미터 (top_p, top_k 등)
            if "top_p" in kwargs:
                body["top_p"] = kwargs["top_p"]
            if "top_k" in kwargs:
                body["top_k"] = kwargs["top_k"]

            # Bedrock 호출
            response = client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())
            latency_ms = (time.time() - start_time) * 1000

            # Claude 3 응답 파싱
            content = result.get("content", [{}])[0].get("text", "")
            usage = result.get("usage", {})

            return LLMResponse(
                content=content,
                model_id=self.model_id,
                provider=self.provider_name,
                prompt_version=prompt_version or "unknown",
                latency_ms=latency_ms,
                usage=LLMUsageMetadata(
                    prompt_tokens=usage.get("input_tokens", 0),
                    completion_tokens=usage.get("output_tokens", 0),
                    total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                ),
                request_id=response["ResponseMetadata"].get("RequestId"),
                raw_response=result,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_message = self._parse_bedrock_error(e)

            return LLMResponse(
                content="",
                model_id=self.model_id,
                provider=self.provider_name,
                prompt_version=prompt_version or "unknown",
                latency_ms=latency_ms,
                error=error_message,
            )

    async def generate_structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        구조화된 JSON 출력 생성

        프롬프트에 JSON 스키마를 추가하여 LLM이 구조화된 응답을 생성하도록 유도

        Args:
            prompt: 사용자 프롬프트
            output_schema: 원하는 JSON 스키마 (dict)
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (낮을수록 결정적)
            prompt_version: 프롬프트 버전
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: JSON 형식의 응답
        """
        import json

        # 스키마를 프롬프트에 추가
        schema_str = json.dumps(output_schema, indent=2, ensure_ascii=False)

        enhanced_system = (system_prompt or "") + f"""

다음 JSON 스키마에 맞춰 응답하세요. 반드시 유효한 JSON만 출력하고 다른 텍스트는 포함하지 마세요.

출력 스키마:
```json
{schema_str}
```

응답 형식: 순수 JSON만 (설명 없이)
"""

        enhanced_prompt = f"""{prompt}

위 요청에 대해 다음 JSON 스키마에 맞춰 응답하세요:
```json
{schema_str}
```
"""

        return await self.generate(
            prompt=enhanced_prompt,
            system_prompt=enhanced_system.strip(),
            max_tokens=max_tokens,
            temperature=temperature,
            prompt_version=prompt_version,
            **kwargs
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ):
        """
        스트리밍 생성

        Note: Bedrock invoke_model_with_response_stream은 복잡하므로
              현재는 non-streaming으로 대체
              향후 필요 시 구현
        """
        # 일단 non-streaming으로 대체
        response = await self.generate(
            prompt, system_prompt, max_tokens, temperature, prompt_version, **kwargs
        )
        yield response.content

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        채팅 (대화 이력 포함)

        Args:
            messages: 대화 이력 [{"role": "user", "content": "..."}]
            max_tokens: 최대 토큰 수
            temperature: 온도
            prompt_version: 프롬프트 버전
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 응답 및 메타데이터
        """
        import json
        start_time = time.time()

        try:
            client = self._get_client()

            # Mock 모드
            if self._mock_mode:
                last_message = messages[-1]["content"] if messages else ""
                return await self._generate_mock(last_message, None, max_tokens, temperature, prompt_version)

            # system 메시지 분리
            system_prompt = None
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    user_messages.append(msg)

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": user_messages,
            }

            if system_prompt:
                body["system"] = system_prompt

            # Bedrock 호출
            response = client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())
            latency_ms = (time.time() - start_time) * 1000

            content = result.get("content", [{}])[0].get("text", "")
            usage = result.get("usage", {})

            return LLMResponse(
                content=content,
                model_id=self.model_id,
                provider=self.provider_name,
                prompt_version=prompt_version or "unknown",
                latency_ms=latency_ms,
                usage=LLMUsageMetadata(
                    prompt_tokens=usage.get("input_tokens", 0),
                    completion_tokens=usage.get("output_tokens", 0),
                    total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                ),
                request_id=response["ResponseMetadata"].get("RequestId"),
                raw_response=result,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_message = self._parse_bedrock_error(e)

            return LLMResponse(
                content="",
                model_id=self.model_id,
                provider=self.provider_name,
                prompt_version=prompt_version or "unknown",
                latency_ms=latency_ms,
                error=error_message,
            )

    async def _generate_mock(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        prompt_version: Optional[str],
    ) -> LLMResponse:
        """
        Mock 모드 응답 생성 (테스트용)

        실제 Bedrock API를 호출하지 않고 더미 응답 반환
        """
        import asyncio

        start_time = time.time()

        # 인위적 지연 (실제 API 시뮬레이션)
        await asyncio.sleep(0.1)

        content = f"[Mock Bedrock Response] Prompt: '{prompt[:50]}...'"
        if system_prompt:
            content += f"\n[System]: {system_prompt[:30]}..."

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=content,
            model_id=self.model_id,
            provider=self.provider_name,
            prompt_version=prompt_version or "unknown",
            latency_ms=latency_ms,
            usage=LLMUsageMetadata(
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(content.split()),
                total_tokens=len(prompt.split()) + len(content.split()),
            ),
        )


# ============================================================================
# Local LLM Provider (Placeholder)
# ============================================================================

class LocalLLMProvider(LLMGateway):
    """
    Local LLM Provider (Placeholder)

    Ollama, llama.cpp 등 로컬 모델 연동용
    향후 구현
    """

    def __init__(self, model_id: str = "llama3", **kwargs):
        super().__init__(model_id, **kwargs)
        self.endpoint = kwargs.get("endpoint", "http://localhost:11434")

    @property
    def provider_name(self) -> str:
        return "local"

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        raise NotImplementedError("LocalLLMProvider is not implemented yet")

    async def generate_stream(self, prompt: str, **kwargs):
        raise NotImplementedError("LocalLLMProvider is not implemented yet")

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        raise NotImplementedError("LocalLLMProvider is not implemented yet")


# ============================================================================
# OpenAI Provider (Placeholder)
# ============================================================================

class OpenAIProvider(LLMGateway):
    """
    OpenAI Provider (Placeholder)

    GPT-4, GPT-3.5 등 OpenAI 모델 연동용
    향후 구현
    """

    def __init__(self, model_id: str = "gpt-4", **kwargs):
        super().__init__(model_id, **kwargs)
        self.api_key = kwargs.get("api_key", os.getenv("OPENAI_API_KEY"))

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        raise NotImplementedError("OpenAIProvider is not implemented yet")

    async def generate_stream(self, prompt: str, **kwargs):
        raise NotImplementedError("OpenAIProvider is not implemented yet")

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        raise NotImplementedError("OpenAIProvider is not implemented yet")


# ============================================================================
# Factory Function
# ============================================================================

def get_llm_gateway(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    **kwargs
) -> LLMGateway:
    """
    LLM Gateway Factory

    환경 변수 기반으로 적절한 Provider를 반환한다.

    환경 변수:
        LLM_PROVIDER: mock | bedrock | local | openai (기본: mock)
        LLM_MODEL_ID: 모델 ID (provider별 기본값 사용)

    Args:
        provider: Provider 이름 (None이면 환경변수 사용)
        model_id: 모델 ID (None이면 provider별 기본값)
        **kwargs: Provider별 추가 설정

    Returns:
        LLMGateway: 선택된 Provider 인스턴스

    Example:
        >>> gateway = get_llm_gateway()  # 환경변수 기반
        >>> gateway = get_llm_gateway(provider="bedrock", model_id="claude-3-sonnet")
        >>> response = await gateway.generate("Hello")
    """
    provider = provider or os.getenv("LLM_PROVIDER", "mock")
    provider = provider.lower()

    if provider == "mock":
        model_id = model_id or os.getenv("LLM_MODEL_ID", "mock-model-v1")
        return MockLLMProvider(model_id=model_id, **kwargs)

    elif provider == "bedrock":
        model_id = model_id or os.getenv(
            "LLM_MODEL_ID",
            "anthropic.claude-3-sonnet-20240229-v1:0"
        )
        return BedrockLLMGateway(model_id=model_id, **kwargs)

    elif provider == "local":
        model_id = model_id or os.getenv("LLM_MODEL_ID", "llama3")
        return LocalLLMProvider(model_id=model_id, **kwargs)

    elif provider == "openai":
        model_id = model_id or os.getenv("LLM_MODEL_ID", "gpt-4")
        return OpenAIProvider(model_id=model_id, **kwargs)

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
