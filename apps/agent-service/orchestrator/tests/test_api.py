"""
Orchestrator API Tests

FastAPI 엔드포인트 통합 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from orchestrator.main import app
from orchestrator.models.parse_response import ParseResponse
from common.models.llm_response import LLMResponse


@pytest.fixture
def client():
    """TestClient 인스턴스"""
    return TestClient(app)


@pytest.fixture
def mock_parser_service():
    """Mock ParserService"""
    service = Mock()
    service.parse_request = AsyncMock()
    return service


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "orchestrator"
    assert "timestamp" in data


def test_root(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "orchestrator"
    assert "supported_request_types" in data
    assert "demand_increase" in data["supported_request_types"]


@patch("orchestrator.main.parser_service")
def test_parse_success(mock_service, client):
    """성공적인 파싱 API 테스트"""
    # Mock 응답
    mock_service.parse_request = AsyncMock(return_value=ParseResponse(
        status="success",
        experiment_spec={
            "experiment_id": "exp-20260507-001",
            "request_id": "req-001",
            "title": "강남구 신호등 최적화",
            "description": "테스트",
            "location": {"region": "강남구"},
            "time_settings": {"start_time": "07:00"},
            "traffic_settings": {"vehicle_count": 5000},
            "objectives": ["목표"],
        },
        missing_fields=None,
        clarification_question=None,
        request_type="signal_timing_change",
        confidence_score=0.9,
        processing_time_ms=1250.5,
        llm_metadata={"model_id": "mock-model"},
    ))

    # API 호출
    response = client.post(
        "/orchestrator/parse",
        json={
            "user_input": "서울 강남구 출퇴근 시간대 신호등 최적화",
            "user_id": "test-user",
        }
    )

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["experiment_spec"] is not None
    assert data["request_type"] == "signal_timing_change"
    assert data["confidence_score"] == 0.9


@patch("orchestrator.main.parser_service")
def test_parse_needs_clarification(mock_service, client):
    """보완 질문 필요 API 테스트"""
    # Mock 응답
    mock_service.parse_request = AsyncMock(return_value=ParseResponse(
        status="needs_clarification",
        experiment_spec=None,
        missing_fields=["location", "time_settings"],
        clarification_question="시뮬레이션할 지역과 시간대를 알려주세요.",
        request_type="demand_increase",
        confidence_score=0.6,
        processing_time_ms=800.0,
        llm_metadata={"model_id": "mock-model"},
    ))

    # API 호출
    response = client.post(
        "/orchestrator/parse",
        json={
            "user_input": "교통량이 증가하면 어떻게 될까요?",
        }
    )

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_clarification"
    assert data["missing_fields"] == ["location", "time_settings"]
    assert data["clarification_question"] is not None


@patch("orchestrator.main.parser_service")
def test_parse_with_rag_context(mock_service, client):
    """RAG 컨텍스트 포함 API 테스트"""
    # Mock 응답
    mock_service.parse_request = AsyncMock(return_value=ParseResponse(
        status="success",
        experiment_spec={
            "experiment_id": "exp-001",
            "request_id": "req-001",
            "title": "테스트",
            "description": "테스트",
            "location": {"region": "강남구"},
            "time_settings": {},
            "traffic_settings": {},
            "objectives": [],
        },
        request_type="lane_change",
        confidence_score=0.85,
        processing_time_ms=1000.0,
    ))

    # API 호출 (RAG 컨텍스트 포함)
    response = client.post(
        "/orchestrator/parse",
        json={
            "user_input": "차로를 추가하면 어떻게 될까요?",
            "user_id": "test-user",
            "rag_contexts": [
                {
                    "context_type": "previous_experiment",
                    "content": "이전 실험 정보",
                    "relevance_score": 0.8,
                    "source": "exp-001"
                }
            ]
        }
    )

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@patch("orchestrator.main.parser_service")
def test_parse_error(mock_service, client):
    """오류 발생 API 테스트"""
    # Mock 응답
    mock_service.parse_request = AsyncMock(return_value=ParseResponse(
        status="error",
        experiment_spec=None,
        error_message="LLM 호출 실패: Timeout",
        processing_time_ms=5000.0,
    ))

    # API 호출
    response = client.post(
        "/orchestrator/parse",
        json={
            "user_input": "테스트",
        }
    )

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error_message"] is not None


@patch("orchestrator.main.parser_service", None)
def test_parse_service_not_initialized(client):
    """서비스 초기화 전 호출 테스트"""
    response = client.post(
        "/orchestrator/parse",
        json={
            "user_input": "테스트",
        }
    )

    # 검증
    assert response.status_code == 503
    assert "not initialized" in response.json()["detail"]


def test_parse_invalid_request(client):
    """잘못된 요청 테스트"""
    # user_input 누락
    response = client.post(
        "/orchestrator/parse",
        json={
            "user_id": "test-user",
        }
    )

    # 검증
    assert response.status_code == 422  # Validation error


@patch("orchestrator.main.agent_logger")
def test_get_logs(mock_logger, client):
    """로그 조회 API 테스트"""
    # Mock 로그
    mock_logger.logs = [
        {
            "log_id": "log-001",
            "level": "info",
            "message": "테스트 로그 1",
        },
        {
            "log_id": "log-002",
            "level": "error",
            "message": "테스트 로그 2",
        },
    ]

    # API 호출
    response = client.get("/orchestrator/logs?limit=10")

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["logs"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
