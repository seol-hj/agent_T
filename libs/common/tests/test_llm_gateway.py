"""
LLM Gateway Tests
"""

import pytest
import asyncio
from ..gateways.llm import (
    get_llm_gateway,
    MockLLMProvider,
    LLMGateway,
)
from ..models.llm_response import LLMResponse


@pytest.mark.asyncio
async def test_mock_provider_generate():
    """Mock Provider 기본 생성 테스트"""
    gateway = get_llm_gateway(provider="mock")

    assert isinstance(gateway, MockLLMProvider)
    assert gateway.provider_name == "mock"

    response = await gateway.generate(
        prompt="Hello, world!",
        prompt_version="v1.0"
    )

    assert isinstance(response, LLMResponse)
    assert response.success
    assert response.model_id == "mock-model-v1"
    assert response.provider == "mock"
    assert response.prompt_version == "v1.0"
    assert response.latency_ms > 0
    assert "Hello, world!" in response.content
    assert response.usage is not None
    assert response.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_mock_provider_with_system_prompt():
    """System prompt 포함 테스트"""
    gateway = get_llm_gateway(provider="mock")

    response = await gateway.generate(
        prompt="What is AI?",
        system_prompt="You are a helpful assistant.",
        temperature=0.5,
    )

    assert response.success
    assert "What is AI?" in response.content
    assert "[System]" in response.content


@pytest.mark.asyncio
async def test_mock_provider_chat():
    """채팅 테스트"""
    gateway = get_llm_gateway(provider="mock")

    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    response = await gateway.chat(messages=messages)

    assert response.success
    assert "How are you?" in response.content


@pytest.mark.asyncio
async def test_mock_provider_streaming():
    """스트리밍 테스트"""
    gateway = get_llm_gateway(provider="mock")

    chunks = []
    async for chunk in gateway.generate_stream(prompt="Stream test"):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert "Mock" in "".join(chunks)


@pytest.mark.asyncio
async def test_metadata_tracking():
    """메타데이터 추적 테스트"""
    gateway = get_llm_gateway(provider="mock")

    response = await gateway.generate(
        prompt="Test metadata",
        prompt_version="scenario-gen-v2.1",
        max_tokens=500,
        temperature=0.7,
    )

    # 필수 메타데이터 확인
    assert response.model_id is not None
    assert response.provider == "mock"
    assert response.prompt_version == "scenario-gen-v2.1"
    assert response.latency_ms >= 0
    assert response.timestamp is not None

    # Dict 변환
    data = response.to_dict()
    assert "model_id" in data
    assert "provider" in data
    assert "prompt_version" in data
    assert "latency_ms" in data
    assert "usage" in data


@pytest.mark.asyncio
async def test_factory_env_var(monkeypatch):
    """환경 변수 기반 Factory 테스트"""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MODEL_ID", "custom-model")

    gateway = get_llm_gateway()

    assert gateway.model_id == "custom-model"
    assert gateway.provider_name == "mock"


@pytest.mark.asyncio
async def test_factory_explicit_params():
    """명시적 파라미터 Factory 테스트"""
    gateway = get_llm_gateway(
        provider="mock",
        model_id="test-model-v3",
        delay_ms=50,
    )

    assert gateway.model_id == "test-model-v3"
    assert gateway.delay_ms == 50


def test_factory_invalid_provider():
    """잘못된 Provider 테스트"""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_gateway(provider="invalid_provider")


@pytest.mark.asyncio
async def test_parallel_requests():
    """병렬 요청 테스트"""
    gateway = get_llm_gateway(provider="mock", delay_ms=50)

    tasks = [
        gateway.generate(f"Request {i}")
        for i in range(5)
    ]

    responses = await asyncio.gather(*tasks)

    assert len(responses) == 5
    for i, response in enumerate(responses):
        assert response.success
        assert f"Request {i}" in response.content


@pytest.mark.asyncio
async def test_usage_metadata():
    """사용량 메타데이터 테스트"""
    gateway = get_llm_gateway(provider="mock")

    response = await gateway.generate("Short prompt")

    assert response.usage is not None
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.usage.total_tokens == (
        response.usage.prompt_tokens + response.usage.completion_tokens
    )
    assert response.total_tokens == response.usage.total_tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
