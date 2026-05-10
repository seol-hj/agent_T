"""
Reporter API Tests

FastAPI 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.gateways.llm import LLMResponse


@pytest.fixture
def mock_storage():
    """Mock Storage Gateway"""
    storage = AsyncMock()
    storage.upload = AsyncMock(return_value="s3://bucket/exp-001/report.md")
    return storage


@pytest.fixture
def mock_llm():
    """Mock LLM Gateway"""
    llm = AsyncMock()

    async def generate_side_effect(request):
        return LLMResponse(
            content="### 정책적 해석\n\nLLM 생성 내용...",
            metadata={"model": "mock"},
        )

    llm.generate = AsyncMock(side_effect=generate_side_effect)
    return llm


@pytest.fixture
def app(mock_storage, mock_llm):
    """테스트용 FastAPI 앱"""
    # common 모듈의 Gateway를 mock
    import common
    original_get_storage = common.get_storage_gateway
    original_get_llm = common.get_llm_gateway
    common.get_storage_gateway = lambda: mock_storage
    common.get_llm_gateway = lambda: mock_llm

    # 앱 임포트 (startup 이벤트 자동 실행됨)
    from reporter.main import app as reporter_app

    yield reporter_app

    # 원래 함수 복원
    common.get_storage_gateway = original_get_storage
    common.get_llm_gateway = original_get_llm


@pytest.fixture
def client(app):
    """테스트 클라이언트"""
    return TestClient(app)


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "reporter"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_readiness_check(client):
    """준비 상태 체크 테스트"""
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "reporter"
    assert "llm_available" in data


def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "reporter"
    assert data["version"] == "0.1.0"
    assert "endpoints" in data
    assert "reporter_types" in data
    assert "report_sections" in data

    # Reporter 타입 확인
    types = {r["type"] for r in data["reporter_types"]}
    assert "template" in types
    assert "llm" in types


def test_generate_report_template(client):
    """템플릿 기반 리포트 생성 테스트"""
    request_data = {
        "report_request": {
            "schema_version": "1.0",
            "request_id": "req-rep-001",
            "experiment_id": "exp-001",
            "analysis_result": {
                "schema_version": "1.0",
                "analysis_id": "ana-001",
                "experiment_id": "exp-001",
                "kpi_comparison": {
                    "baseline_kpis": {
                        "average_travel_time": 125.0,
                        "average_waiting_time": 12.0,
                    },
                    "alternative_kpis": {
                        "average_travel_time": 110.0,
                        "average_waiting_time": 9.6,
                    },
                    "improvements": {
                        "average_travel_time": 12.0,
                        "average_waiting_time": 20.0,
                    },
                },
                "overall_score": 13.5,
                "summary": "Alternative 시나리오가 우수합니다.",
            }
        },
        "reporter_type": "template"
    }

    response = client.post("/report/generate", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    assert artifact["schema_version"] == "1.0"
    assert artifact["request_id"] == "req-rep-001"
    assert artifact["experiment_id"] == "exp-001"
    assert artifact["report_uri"] == "s3://bucket/exp-001/report.md"
    assert artifact["report_format"] == "markdown"
    assert "sections" in artifact
    assert "generated_by" in artifact


def test_generate_report_llm(client):
    """LLM 기반 리포트 생성 테스트"""
    request_data = {
        "report_request": {
            "schema_version": "1.0",
            "request_id": "req-rep-002",
            "experiment_id": "exp-002",
            "analysis_result": {
                "schema_version": "1.0",
                "analysis_id": "ana-002",
                "experiment_id": "exp-002",
                "kpi_comparison": {
                    "baseline_kpis": {"average_travel_time": 125.0},
                    "alternative_kpis": {"average_travel_time": 110.0},
                    "improvements": {"average_travel_time": 12.0},
                },
                "overall_score": 13.5,
                "summary": "개선됨",
            }
        },
        "reporter_type": "llm"
    }

    response = client.post("/report/generate", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    assert "llmreporter" in artifact["generated_by"].lower()


def test_generate_report_with_user_request(client):
    """사용자 요청 포함 리포트 생성"""
    request_data = {
        "report_request": {
            "schema_version": "1.0",
            "request_id": "req-rep-003",
            "experiment_id": "exp-003",
            "analysis_result": {
                "schema_version": "1.0",
                "analysis_id": "ana-003",
                "experiment_id": "exp-003",
                "kpi_comparison": {
                    "baseline_kpis": {},
                    "alternative_kpis": {},
                    "improvements": {},
                },
                "overall_score": 0.0,
                "summary": "테스트",
            },
            "user_request": "교통 수요 20% 증가 시나리오",
        },
        "reporter_type": "template"
    }

    response = client.post("/report/generate", json=request_data)
    assert response.status_code == 200


def test_generate_report_with_experiment_context(client):
    """실험 컨텍스트 포함 리포트 생성"""
    request_data = {
        "report_request": {
            "schema_version": "1.0",
            "request_id": "req-rep-004",
            "experiment_id": "exp-004",
            "analysis_result": {
                "schema_version": "1.0",
                "analysis_id": "ana-004",
                "experiment_id": "exp-004",
                "kpi_comparison": {
                    "baseline_kpis": {},
                    "alternative_kpis": {},
                    "improvements": {},
                },
                "overall_score": 0.0,
                "summary": "테스트",
            },
            "experiment_context": {
                "request_type": "lane_change",
                "lane_change": "+1",
                "region": "서울",
            },
        },
        "reporter_type": "template"
    }

    response = client.post("/report/generate", json=request_data)
    assert response.status_code == 200


def test_generate_report_invalid_type(client):
    """잘못된 Reporter 타입 테스트"""
    request_data = {
        "report_request": {
            "schema_version": "1.0",
            "request_id": "req-rep-005",
            "experiment_id": "exp-005",
            "analysis_result": {
                "schema_version": "1.0",
                "analysis_id": "ana-005",
                "experiment_id": "exp-005",
                "kpi_comparison": {},
                "overall_score": 0.0,
                "summary": "",
            },
        },
        "reporter_type": "invalid"
    }

    response = client.post("/report/generate", json=request_data)
    assert response.status_code == 400


def test_report_sections(client):
    """리포트 섹션 확인"""
    request_data = {
        "report_request": {
            "schema_version": "1.0",
            "request_id": "req-rep-006",
            "experiment_id": "exp-006",
            "analysis_result": {
                "schema_version": "1.0",
                "analysis_id": "ana-006",
                "experiment_id": "exp-006",
                "kpi_comparison": {
                    "baseline_kpis": {},
                    "alternative_kpis": {},
                    "improvements": {},
                },
                "overall_score": 0.0,
                "summary": "",
            },
        },
        "reporter_type": "template"
    }

    response = client.post("/report/generate", json=request_data)
    assert response.status_code == 200

    artifact = response.json()
    sections = artifact["sections"]

    # 필수 섹션 확인
    assert "요약" in sections
    assert "기준 시나리오 결과" in sections
    assert "대안 시나리오 결과" in sections
    assert "개선율" in sections
    assert "정책적 해석" in sections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
