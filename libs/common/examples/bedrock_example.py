"""
Bedrock Provider 사용 예시

실제 AWS Bedrock API 호출 예시
"""

import asyncio
import os
from pathlib import Path
import sys

# Common library를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import get_llm_gateway


async def example_basic_generate():
    """기본 텍스트 생성 예시"""
    print("\n=== 기본 텍스트 생성 ===\n")

    # 환경 변수로 Provider 선택
    # export LLM_PROVIDER=bedrock
    # export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
    # export AWS_REGION=ap-northeast-2

    llm = get_llm_gateway()

    response = await llm.generate(
        prompt="교통 시뮬레이션이란 무엇인가요?",
        system_prompt="당신은 교통 공학 전문가입니다. 간결하게 답변하세요.",
        max_tokens=500,
        temperature=0.7,
        prompt_version="basic-v1.0",
    )

    print(f"Provider: {response.provider}")
    print(f"Model: {response.model_id}")
    print(f"Prompt Version: {response.prompt_version}")
    print(f"Latency: {response.latency_ms:.2f}ms")
    print(f"Tokens: {response.total_tokens}")
    print(f"\n응답:\n{response.content}\n")

    return response


async def example_structured_output():
    """구조화된 JSON 출력 예시"""
    print("\n=== 구조화된 JSON 출력 ===\n")

    llm = get_llm_gateway()

    output_schema = {
        "location": {
            "type": "string",
            "description": "시뮬레이션 위치"
        },
        "duration_hours": {
            "type": "number",
            "description": "시뮬레이션 시간(시간)"
        },
        "vehicle_count": {
            "type": "number",
            "description": "예상 차량 수"
        },
        "objectives": {
            "type": "array",
            "description": "시뮬레이션 목표 리스트"
        }
    }

    response = await llm.generate_structured_output(
        prompt="서울 강남구 출퇴근 시간대 교통 시뮬레이션 시나리오를 생성하세요",
        output_schema=output_schema,
        system_prompt="당신은 교통 시나리오 생성 전문가입니다.",
        temperature=0.3,  # 더 결정적인 출력
        prompt_version="scenario-gen-v2.0",
    )

    print(f"Latency: {response.latency_ms:.2f}ms")
    print(f"\nJSON 응답:\n{response.content}\n")

    return response


async def example_chat():
    """대화 이력 포함 채팅 예시"""
    print("\n=== 대화 이력 포함 채팅 ===\n")

    llm = get_llm_gateway()

    messages = [
        {"role": "system", "content": "당신은 교통 시뮬레이션 전문가입니다."},
        {"role": "user", "content": "SUMO가 무엇인가요?"},
        {"role": "assistant", "content": "SUMO는 Simulation of Urban MObility의 약자로, 오픈소스 교통 시뮬레이터입니다."},
        {"role": "user", "content": "SUMO로 어떤 분석을 할 수 있나요?"},
    ]

    response = await llm.chat(
        messages=messages,
        max_tokens=500,
        temperature=0.7,
        prompt_version="chat-v1.0",
    )

    print(f"Latency: {response.latency_ms:.2f}ms")
    print(f"\n응답:\n{response.content}\n")

    return response


async def example_error_handling():
    """에러 처리 예시"""
    print("\n=== 에러 처리 ===\n")

    # 잘못된 모델 ID로 테스트
    from common.gateways.llm import BedrockProvider

    llm = BedrockProvider(
        model_id="invalid-model-id",
        region="ap-northeast-2"
    )

    response = await llm.generate(
        prompt="Test",
        prompt_version="error-test-v1.0"
    )

    if response.success:
        print(f"응답: {response.content}")
    else:
        print(f"에러 발생: {response.error}")
        print(f"Latency: {response.latency_ms:.2f}ms")

    return response


async def example_mock_mode():
    """Mock 모드 예시 (Bedrock API 호출 없이 테스트)"""
    print("\n=== Mock 모드 ===\n")

    from common.gateways.llm import BedrockProvider

    llm = BedrockProvider(
        model_id="test-model",
        mock_mode=True
    )

    response = await llm.generate(
        prompt="Mock 모드 테스트",
        prompt_version="mock-test-v1.0"
    )

    print(f"Provider: {response.provider}")
    print(f"Model: {response.model_id}")
    print(f"Latency: {response.latency_ms:.2f}ms")
    print(f"\n응답:\n{response.content}\n")

    return response


async def example_with_retry():
    """Retry 설정 예시"""
    print("\n=== Retry 설정 ===\n")

    from common.gateways.llm import BedrockProvider

    llm = BedrockProvider(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        region="ap-northeast-2",
        timeout=30,
        max_retries=5,  # 최대 5번 재시도
    )

    print(f"Timeout: {llm.timeout}초")
    print(f"Max Retries: {llm.max_retries}")

    response = await llm.generate(
        prompt="간단한 테스트",
        prompt_version="retry-test-v1.0"
    )

    print(f"Success: {response.success}")
    print(f"Latency: {response.latency_ms:.2f}ms\n")

    return response


async def example_metadata_logging():
    """메타데이터 로깅 예시"""
    print("\n=== 메타데이터 로깅 ===\n")

    llm = get_llm_gateway()

    response = await llm.generate(
        prompt="메타데이터 로깅 테스트",
        prompt_version="logging-test-v1.0"
    )

    # 로그에 기록할 메타데이터
    log_data = {
        "timestamp": response.timestamp.isoformat(),
        "model_id": response.model_id,
        "provider": response.provider,
        "prompt_version": response.prompt_version,
        "latency_ms": response.latency_ms,
        "tokens": {
            "prompt": response.usage.prompt_tokens if response.usage else 0,
            "completion": response.usage.completion_tokens if response.usage else 0,
            "total": response.total_tokens,
        },
        "request_id": response.request_id,
        "success": response.success,
    }

    print("로깅할 메타데이터:")
    import json
    print(json.dumps(log_data, indent=2, ensure_ascii=False))

    return response


async def main():
    """모든 예시 실행"""
    print("=" * 60)
    print("Bedrock Provider 사용 예시")
    print("=" * 60)

    # 환경 변수 확인
    provider = os.getenv("LLM_PROVIDER", "mock")
    print(f"\nLLM_PROVIDER: {provider}")
    print(f"AWS_REGION: {os.getenv('AWS_REGION', 'not set')}")
    print(f"BEDROCK_MODEL_ID: {os.getenv('BEDROCK_MODEL_ID', 'not set')}")

    if provider == "bedrock":
        print("\n⚠️  실제 AWS Bedrock API를 호출합니다. 비용이 발생할 수 있습니다.")
        print("Mock 모드로 테스트하려면: export LLM_PROVIDER=mock")
        input("\n계속하려면 Enter를 누르세요...")

    try:
        # Mock 모드는 항상 실행
        await example_mock_mode()

        # Bedrock 모드일 때만 실제 API 호출
        if provider == "bedrock":
            await example_basic_generate()
            await example_structured_output()
            await example_chat()
            await example_with_retry()
            await example_metadata_logging()

            # 에러 처리는 선택적으로
            # await example_error_handling()
        else:
            print("\n실제 Bedrock API 호출 예시를 실행하려면:")
            print("export LLM_PROVIDER=bedrock")
            print("export AWS_REGION=ap-northeast-2")
            print("export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0")

    except Exception as e:
        print(f"\n에러 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
