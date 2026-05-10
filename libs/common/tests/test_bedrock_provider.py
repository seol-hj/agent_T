"""
Bedrock Provider Tests (Mock boto3 client)
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO

from ..gateways.llm import BedrockProvider, LLMResponse


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock Runtime 클라이언트"""
    client = Mock()

    # Mock invoke_model 응답
    def mock_invoke_model(modelId, body):
        # Request body 파싱
        request_body = json.loads(body)

        # Mock 응답 생성
        response_data = {
            "content": [
                {
                    "text": f"Mock response for: {request_body['messages'][0]['content'][:50]}"
                }
            ],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
            },
            "stop_reason": "end_turn",
        }

        # BytesIO로 감싸기 (실제 Bedrock 응답 형식)
        body_stream = BytesIO(json.dumps(response_data).encode())

        return {
            "body": body_stream,
            "ResponseMetadata": {
                "RequestId": "mock-request-id-123",
                "HTTPStatusCode": 200,
            }
        }

    client.invoke_model = Mock(side_effect=mock_invoke_model)

    return client


@pytest.mark.asyncio
async def test_bedrock_provider_initialization():
    """BedrockProvider 초기화 테스트"""
    provider = BedrockProvider(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        region="ap-northeast-2",
        timeout=30,
        max_retries=2,
    )

    assert provider.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
    assert provider.region == "ap-northeast-2"
    assert provider.timeout == 30
    assert provider.max_retries == 2
    assert provider.provider_name == "bedrock"


@pytest.mark.asyncio
async def test_bedrock_generate_with_mock_client(mock_bedrock_client):
    """Mock boto3 client로 generate 테스트"""
    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_bedrock_client

    response = await provider.generate(
        prompt="Hello, how are you?",
        system_prompt="You are a helpful assistant.",
        max_tokens=500,
        temperature=0.7,
        prompt_version="test-v1.0",
    )

    # 응답 검증
    assert isinstance(response, LLMResponse)
    assert response.success
    assert "Mock response for: Hello, how are you?" in response.content
    assert response.model_id == provider.model_id
    assert response.provider == "bedrock"
    assert response.prompt_version == "test-v1.0"
    assert response.latency_ms > 0
    assert response.usage.prompt_tokens == 100
    assert response.usage.completion_tokens == 50
    assert response.usage.total_tokens == 150
    assert response.request_id == "mock-request-id-123"

    # boto3 호출 확인
    mock_bedrock_client.invoke_model.assert_called_once()


@pytest.mark.asyncio
async def test_bedrock_chat_with_mock_client(mock_bedrock_client):
    """Chat 메서드 테스트"""
    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_bedrock_client

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    response = await provider.chat(
        messages=messages,
        max_tokens=500,
        temperature=0.7,
        prompt_version="chat-v1.0",
    )

    assert response.success
    assert "Mock response" in response.content
    assert response.prompt_version == "chat-v1.0"


@pytest.mark.asyncio
async def test_bedrock_mock_mode():
    """Mock 모드 테스트 (실제 boto3 호출 없음)"""
    provider = BedrockProvider(
        model_id="test-model",
        mock_mode=True
    )

    response = await provider.generate(
        prompt="Test prompt",
        prompt_version="mock-test-v1.0"
    )

    assert response.success
    assert "[Mock Bedrock Response]" in response.content
    assert "Test prompt" in response.content
    assert response.model_id == "test-model"
    assert response.provider == "bedrock"


@pytest.mark.asyncio
async def test_bedrock_error_handling():
    """에러 처리 테스트"""
    mock_client = Mock()

    # ValidationException 시뮬레이션
    def raise_validation_error(*args, **kwargs):
        from botocore.exceptions import ClientError
        raise ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid model ID"}},
            "InvokeModel"
        )

    mock_client.invoke_model = Mock(side_effect=raise_validation_error)

    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_client

    response = await provider.generate("Test prompt")

    assert not response.success
    assert response.error is not None
    assert "검증 오류" in response.error or "ValidationException" in response.error


@pytest.mark.asyncio
async def test_bedrock_throttling_error():
    """ThrottlingException 테스트"""
    mock_client = Mock()

    def raise_throttling_error(*args, **kwargs):
        from botocore.exceptions import ClientError
        raise ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )

    mock_client.invoke_model = Mock(side_effect=raise_throttling_error)

    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_client

    response = await provider.generate("Test")

    assert not response.success
    assert "제한 초과" in response.error or "ThrottlingException" in response.error


@pytest.mark.asyncio
async def test_bedrock_access_denied_error():
    """AccessDeniedException 테스트"""
    mock_client = Mock()

    def raise_access_denied(*args, **kwargs):
        from botocore.exceptions import ClientError
        raise ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "InvokeModel"
        )

    mock_client.invoke_model = Mock(side_effect=raise_access_denied)

    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_client

    response = await provider.generate("Test")

    assert not response.success
    assert "권한" in response.error or "AccessDeniedException" in response.error


@pytest.mark.asyncio
async def test_bedrock_structured_output(mock_bedrock_client):
    """구조화된 출력 생성 테스트"""
    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_bedrock_client

    output_schema = {
        "location": "string",
        "duration_hours": "number",
        "vehicle_count": "number",
    }

    response = await provider.generate_structured_output(
        prompt="서울 강남구 출퇴근 시간대 시뮬레이션",
        output_schema=output_schema,
        prompt_version="scenario-gen-v2.0",
    )

    assert response.success
    assert response.content is not None
    # 프롬프트에 스키마가 포함되어 있는지 확인 (간접적으로)
    mock_bedrock_client.invoke_model.assert_called()


@pytest.mark.asyncio
async def test_bedrock_generate_stream(mock_bedrock_client):
    """스트리밍 생성 테스트 (현재는 non-streaming)"""
    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_bedrock_client

    chunks = []
    async for chunk in provider.generate_stream(prompt="Stream test"):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert "Mock response" in "".join(chunks)


@pytest.mark.asyncio
async def test_bedrock_env_var_config(monkeypatch):
    """환경 변수 기반 설정 테스트"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "custom-model-id")
    monkeypatch.setenv("BEDROCK_TIMEOUT", "120")
    monkeypatch.setenv("BEDROCK_MAX_RETRIES", "5")

    provider = BedrockProvider()

    assert provider.region == "us-east-1"
    assert provider.timeout == 120
    assert provider.max_retries == 5


@pytest.mark.asyncio
async def test_bedrock_no_credentials_error():
    """Credentials 없을 때 에러 처리"""
    mock_client = Mock()

    def raise_no_credentials(*args, **kwargs):
        from botocore.exceptions import NoCredentialsError
        raise NoCredentialsError()

    mock_client.invoke_model = Mock(side_effect=raise_no_credentials)

    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_client

    response = await provider.generate("Test")

    assert not response.success
    assert "인증 실패" in response.error or "Credentials" in response.error


@pytest.mark.asyncio
async def test_bedrock_timeout_error():
    """타임아웃 에러 처리"""
    mock_client = Mock()

    def raise_timeout(*args, **kwargs):
        from botocore.exceptions import ConnectTimeoutError
        raise ConnectTimeoutError(endpoint_url="https://bedrock-runtime.ap-northeast-2.amazonaws.com")

    mock_client.invoke_model = Mock(side_effect=raise_timeout)

    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_client

    response = await provider.generate("Test")

    assert not response.success
    assert "연결 실패" in response.error or "Timeout" in response.error


@pytest.mark.asyncio
async def test_bedrock_parse_error_messages():
    """에러 메시지 파싱 테스트"""
    provider = BedrockProvider()

    # ValidationException
    from botocore.exceptions import ClientError
    error = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Test"}},
        "InvokeModel"
    )
    message = provider._parse_bedrock_error(error)
    assert "검증 오류" in message

    # ThrottlingException
    error = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "Test"}},
        "InvokeModel"
    )
    message = provider._parse_bedrock_error(error)
    assert "제한 초과" in message

    # ResourceNotFoundException
    error = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Test"}},
        "InvokeModel"
    )
    message = provider._parse_bedrock_error(error)
    assert "모델 없음" in message


@pytest.mark.asyncio
async def test_bedrock_metadata_tracking(mock_bedrock_client):
    """메타데이터 추적 테스트"""
    provider = BedrockProvider(mock_mode=False)
    provider._client = mock_bedrock_client

    response = await provider.generate(
        prompt="Test metadata tracking",
        prompt_version="metadata-test-v1.5",
    )

    # 필수 메타데이터 확인
    assert response.model_id is not None
    assert response.provider == "bedrock"
    assert response.prompt_version == "metadata-test-v1.5"
    assert response.latency_ms >= 0
    assert response.timestamp is not None
    assert response.request_id == "mock-request-id-123"

    # Usage 메타데이터
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.total_tokens > 0

    # Dict 변환
    data = response.to_dict()
    assert "model_id" in data
    assert "provider" in data
    assert "prompt_version" in data
    assert "latency_ms" in data
    assert "request_id" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
