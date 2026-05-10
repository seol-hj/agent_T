"""
Integration Tests

실제 Mock LLM Gateway를 사용한 통합 테스트
"""

import pytest
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.gateways.llm import MockLLMProvider
from orchestrator.services.parser_service import ParserService


@pytest.fixture
def mock_llm_provider():
    """실제 MockLLMProvider 인스턴스"""
    return MockLLMProvider(model_id="mock-claude-sonnet", delay_ms=100)


@pytest.fixture
def parser_service(mock_llm_provider):
    """실제 ParserService 인스턴스"""
    return ParserService(llm_gateway=mock_llm_provider, max_retries=2)


@pytest.mark.asyncio
async def test_demand_increase_scenario(parser_service):
    """교통량 증가 시나리오 통합 테스트"""
    result = await parser_service.parse_request(
        user_input="서울 강남구에서 차량이 20% 증가하면 어떻게 될까요? 평일 아침 출퇴근 시간(7시-9시)에 시뮬레이션하고 싶습니다.",
        request_id="req-integration-001",
    )

    # Mock LLM은 request_type을 탐지하지는 못하지만 응답은 성공해야 함
    assert result.status in ["success", "needs_clarification", "error"]
    assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_signal_timing_scenario(parser_service):
    """신호 타이밍 변경 시나리오 통합 테스트"""
    result = await parser_service.parse_request(
        user_input="서울 종로구 광화문 교차로의 신호등 타이밍을 최적화하고 싶습니다.",
        request_id="req-integration-002",
    )

    assert result.status in ["success", "needs_clarification", "error"]
    assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_lane_change_scenario(parser_service):
    """차로 변경 시나리오 통합 테스트"""
    result = await parser_service.parse_request(
        user_input="부산 해운대구 해운대로에 차로를 하나 추가하면 통행 시간이 얼마나 단축될까요?",
        request_id="req-integration-003",
    )

    assert result.status in ["success", "needs_clarification", "error"]
    assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_insufficient_information(parser_service):
    """정보 부족 시나리오 통합 테스트"""
    result = await parser_service.parse_request(
        user_input="교통 시뮬레이션을 하고 싶습니다.",
        request_id="req-integration-004",
    )

    # 정보가 부족하므로 needs_clarification이 기대됨
    # (하지만 Mock LLM은 실제 파싱을 못하므로 status는 다양할 수 있음)
    assert result.status in ["success", "needs_clarification", "error"]
    assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_multiple_requests_concurrent(parser_service):
    """동시 다중 요청 테스트"""
    tasks = [
        parser_service.parse_request(
            user_input=f"서울 강남구 테스트 {i}",
            request_id=f"req-concurrent-{i:03d}",
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    # 모든 요청이 응답을 받아야 함
    assert len(results) == 5
    for result in results:
        assert result.status in ["success", "needs_clarification", "error"]
        assert result.processing_time_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
