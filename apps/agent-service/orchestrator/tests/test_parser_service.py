"""
Parser Service Tests

ParserService 단위 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.models.llm_response import LLMResponse, LLMUsageMetadata
from orchestrator.services.parser_service import ParserService
from orchestrator.models.parse_response import RAGContext


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway"""
    gateway = Mock()
    gateway.generate = AsyncMock()
    return gateway


@pytest.fixture
def parser_service(mock_llm_gateway):
    """ParserService 인스턴스"""
    return ParserService(llm_gateway=mock_llm_gateway, max_retries=3)


@pytest.mark.asyncio
async def test_parse_request_success(parser_service, mock_llm_gateway):
    """성공적인 파싱 테스트"""
    # Mock LLM 응답
    mock_response = LLMResponse(
        content="""```json
{
  "request_type": "signal_timing_change",
  "confidence_score": 0.9,
  "experiment_spec": {
    "experiment_id": "exp-20260507-001",
    "request_id": "req-001",
    "title": "강남구 신호등 최적화",
    "description": "출퇴근 시간대 교통 혼잡 완화",
    "location": {
      "region": "서울특별시 강남구",
      "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
      "osm_query": "Gangnam-gu, Seoul, South Korea"
    },
    "time_settings": {
      "start_time": "07:00",
      "end_time": "09:00",
      "duration_hours": 2,
      "time_period": "weekday_morning_rush"
    },
    "traffic_settings": {
      "vehicle_count": 5000,
      "vehicle_types": ["passenger", "bus", "truck"],
      "vehicle_distribution": {"passenger": 0.8, "bus": 0.1, "truck": 0.1},
      "demand_level": "high"
    },
    "objectives": ["통행 시간 단축", "배출량 감소"],
    "constraints": []
  },
  "missing_fields": null,
  "clarification_question": null
}
```""",
        model_id="anthropic.claude-3-sonnet",
        provider="bedrock",
        prompt_version="experiment-parser-v1.0",
        latency_ms=1250.5,
        usage=LLMUsageMetadata(input_tokens=1200, output_tokens=450),
        success=True,
    )
    mock_llm_gateway.generate.return_value = mock_response

    # 파싱 실행
    result = await parser_service.parse_request(
        user_input="서울 강남구 출퇴근 시간대 신호등 최적화 효과 분석",
        request_id="req-001",
    )

    # 검증
    assert result.status == "success"
    assert result.experiment_spec is not None
    assert result.experiment_spec["title"] == "강남구 신호등 최적화"
    assert result.request_type == "signal_timing_change"
    assert result.confidence_score == 0.9
    assert result.missing_fields is None
    assert result.clarification_question is None
    assert result.llm_metadata is not None
    assert result.llm_metadata["model_id"] == "anthropic.claude-3-sonnet"


@pytest.mark.asyncio
async def test_parse_request_needs_clarification(parser_service, mock_llm_gateway):
    """보완 질문이 필요한 경우 테스트"""
    # Mock LLM 응답 (location 누락)
    mock_response = LLMResponse(
        content="""```json
{
  "request_type": "demand_increase",
  "confidence_score": 0.6,
  "experiment_spec": null,
  "missing_fields": ["location", "time_settings.start_time"],
  "clarification_question": "시뮬레이션할 지역과 시간대를 알려주세요."
}
```""",
        model_id="mock-model",
        provider="mock",
        latency_ms=500.0,
        success=True,
    )
    mock_llm_gateway.generate.return_value = mock_response

    # 파싱 실행
    result = await parser_service.parse_request(
        user_input="교통량이 증가하면 어떻게 될까요?",
        request_id="req-002",
    )

    # 검증
    assert result.status == "needs_clarification"
    assert result.experiment_spec is None
    assert result.missing_fields == ["location", "time_settings.start_time"]
    assert result.clarification_question is not None
    assert "지역" in result.clarification_question or "시간대" in result.clarification_question


@pytest.mark.asyncio
async def test_parse_request_with_rag_context(parser_service, mock_llm_gateway):
    """RAG 컨텍스트 포함 테스트"""
    # Mock LLM 응답
    mock_response = LLMResponse(
        content="""```json
{
  "request_type": "lane_change",
  "confidence_score": 0.85,
  "experiment_spec": {
    "experiment_id": "exp-20260507-002",
    "request_id": "req-003",
    "title": "강남구 테헤란로 차로 추가",
    "description": "3차로를 4차로로 확장 효과 분석",
    "location": {
      "region": "서울특별시 강남구 테헤란로",
      "osm_query": "Teheran-ro, Gangnam-gu, Seoul"
    },
    "time_settings": {
      "start_time": "07:00",
      "end_time": "09:00",
      "duration_hours": 2,
      "time_period": "weekday_morning_rush"
    },
    "traffic_settings": {
      "vehicle_count": 5000,
      "demand_level": "high"
    },
    "objectives": ["통행 시간 단축"],
    "constraints": ["기존 인프라 유지"]
  },
  "missing_fields": null,
  "clarification_question": null
}
```""",
        model_id="mock-model",
        provider="mock",
        latency_ms=800.0,
        success=True,
    )
    mock_llm_gateway.generate.return_value = mock_response

    # RAG 컨텍스트 준비
    rag_contexts = [
        RAGContext(
            context_type="previous_experiment",
            content="이전 실험에서 강남구 테헤란로를 분석한 적이 있습니다.",
            relevance_score=0.8,
            source="experiment-exp-001",
        )
    ]

    # 파싱 실행
    result = await parser_service.parse_request(
        user_input="테헤란로 차로를 추가하면 어떻게 될까요?",
        request_id="req-003",
        rag_contexts=rag_contexts,
    )

    # 검증
    assert result.status == "success"
    assert result.experiment_spec is not None
    assert "테헤란로" in result.experiment_spec["title"]


@pytest.mark.asyncio
async def test_parse_request_llm_error(parser_service, mock_llm_gateway):
    """LLM 호출 오류 테스트"""
    # Mock LLM 오류
    mock_response = LLMResponse(
        content="",
        model_id="mock-model",
        provider="mock",
        latency_ms=100.0,
        success=False,
        error="Bedrock API timeout",
    )
    mock_llm_gateway.generate.return_value = mock_response

    # 파싱 실행
    result = await parser_service.parse_request(
        user_input="테스트 입력",
        request_id="req-004",
    )

    # 검증
    assert result.status == "error"
    assert result.error_message is not None
    assert "LLM 호출 실패" in result.error_message or "timeout" in result.error_message.lower()


@pytest.mark.asyncio
async def test_parse_request_validation_retry(parser_service, mock_llm_gateway):
    """Pydantic 검증 실패 후 재시도 테스트"""
    # 첫 번째 시도: 잘못된 JSON (title 누락)
    first_response = LLMResponse(
        content="""```json
{
  "request_type": "demand_increase",
  "confidence_score": 0.7,
  "experiment_spec": {
    "experiment_id": "exp-001",
    "request_id": "req-005",
    "description": "설명만 있음"
  },
  "missing_fields": null,
  "clarification_question": null
}
```""",
        model_id="mock-model",
        provider="mock",
        latency_ms=500.0,
        success=True,
    )

    # 두 번째 시도: 올바른 JSON
    second_response = LLMResponse(
        content="""```json
{
  "request_type": "demand_increase",
  "confidence_score": 0.7,
  "experiment_spec": {
    "experiment_id": "exp-20260507-005",
    "request_id": "req-005",
    "title": "교통량 증가 분석",
    "description": "차량 수 증가 시나리오",
    "location": {"region": "서울 강남구"},
    "time_settings": {"start_time": "07:00", "end_time": "09:00"},
    "traffic_settings": {"vehicle_count": 6000},
    "objectives": ["혼잡도 분석"]
  },
  "missing_fields": null,
  "clarification_question": null
}
```""",
        model_id="mock-model",
        provider="mock",
        latency_ms=600.0,
        success=True,
    )

    mock_llm_gateway.generate.side_effect = [first_response, second_response]

    # 파싱 실행
    result = await parser_service.parse_request(
        user_input="차량이 더 많아지면 어떻게 될까요?",
        request_id="req-005",
    )

    # 검증: 재시도 후 성공
    assert result.status == "success"
    assert result.experiment_spec is not None
    assert mock_llm_gateway.generate.call_count == 2


@pytest.mark.asyncio
async def test_generate_clarification_question():
    """보완 질문 생성 테스트"""
    from orchestrator.prompts.experiment_parser import generate_clarification_question

    # 단일 필드 누락
    question = generate_clarification_question(["location"])
    assert "지역" in question or "위치" in question

    # 복수 필드 누락
    question = generate_clarification_question(["location", "time_settings.start_time"])
    assert "1." in question and "2." in question


def test_extract_json():
    """JSON 추출 테스트"""
    from orchestrator.services.parser_service import ParserService

    mock_llm = Mock()
    service = ParserService(llm_gateway=mock_llm)

    # Case 1: ```json``` 블록
    content1 = """```json
{"key": "value"}
```"""
    assert service._extract_json(content1) == {"key": "value"}

    # Case 2: ``` 블록
    content2 = """```
{"key": "value"}
```"""
    assert service._extract_json(content2) == {"key": "value"}

    # Case 3: 순수 JSON
    content3 = '{"key": "value"}'
    assert service._extract_json(content3) == {"key": "value"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
