"""
LLM Reporter Tests

LLMReporter 단위 테스트
"""

import pytest
from unittest.mock import AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.gateways.llm import LLMResponse
from reporter.reporters.llm_reporter import LLMReporter


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway"""
    llm = AsyncMock()

    # generate 메서드 mock
    async def generate_side_effect(request):
        return LLMResponse(
            content="""### 정책적 해석

Alternative 시나리오는 교통 효율성 측면에서 유의미한 개선을 보여줍니다. 평균 통행 시간이 12% 감소하고 대기 시간이 20% 단축되었습니다.

### 권고사항

- 단계적 시범 적용 권장
- 실시간 모니터링 체계 구축
- 주민 의견 수렴 필요

### 주의사항

- 시뮬레이션 결과와 실제 상황의 차이 고려 필요
- 비용-편익 분석 추가 검토 요망""",
            metadata={"model": "mock-model"},
        )

    llm.generate = AsyncMock(side_effect=generate_side_effect)
    return llm


@pytest.fixture
def reporter(mock_llm_gateway):
    """LLMReporter 인스턴스"""
    return LLMReporter(llm_gateway=mock_llm_gateway)


@pytest.fixture
def analysis_result():
    """샘플 AnalysisResult"""
    return {
        "schema_version": "1.0",
        "analysis_id": "ana-001",
        "experiment_id": "exp-001",
        "kpi_comparison": {
            "baseline_kpis": {
                "average_travel_time": 125.0,
                "average_waiting_time": 12.0,
                "average_speed": 4.16,
                "total_co2": 16590.0,
            },
            "alternative_kpis": {
                "average_travel_time": 110.0,
                "average_waiting_time": 9.6,
                "average_speed": 4.58,
                "total_co2": 14931.0,
            },
            "improvements": {
                "average_travel_time": 12.0,
                "average_waiting_time": 20.0,
                "average_speed": 10.1,
                "total_co2": 10.0,
            },
        },
        "overall_score": 13.5,
        "summary": "Alternative 시나리오가 전반적으로 우수합니다.",
    }


@pytest.mark.asyncio
async def test_generate_report_with_llm(reporter, analysis_result, mock_llm_gateway):
    """LLM 기반 리포트 생성 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    assert content.markdown is not None
    assert len(content.markdown) > 0

    # LLM이 호출되었는지 확인
    assert mock_llm_gateway.generate.called


@pytest.mark.asyncio
async def test_llm_interpretation_included(reporter, analysis_result):
    """LLM 정책적 해석 포함 확인"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    markdown = content.markdown

    # LLM 생성 콘텐츠 포함 확인
    assert "정책적 해석" in markdown
    assert "권고사항" in markdown or "주의사항" in markdown


@pytest.mark.asyncio
async def test_generate_with_user_request(reporter, analysis_result):
    """사용자 요청 포함 테스트"""
    user_request = "차선을 1개 추가했을 때의 효과를 분석해주세요."

    content = await reporter.generate_report(
        analysis_result=analysis_result,
        user_request=user_request,
    )

    markdown = content.markdown
    assert user_request in markdown


@pytest.mark.asyncio
async def test_generate_with_rag_contexts(reporter, analysis_result, mock_llm_gateway):
    """RAG 컨텍스트 포함 테스트"""
    rag_contexts = [
        {"content": "참고: 유사 지역의 사례 연구 결과..."},
        {"content": "참고: 교통 정책 가이드라인..."},
    ]

    content = await reporter.generate_report(
        analysis_result=analysis_result,
        rag_contexts=rag_contexts,
    )

    # LLM 호출 시 RAG 컨텍스트가 프롬프트에 포함되었는지 확인
    assert mock_llm_gateway.generate.called
    call_args = mock_llm_gateway.generate.call_args[0][0]
    assert "참고 자료" in call_args.user_prompt or "참고:" in call_args.user_prompt


@pytest.mark.asyncio
async def test_markdown_structure_with_llm(reporter, analysis_result):
    """LLM 리포트 Markdown 구조 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    markdown = content.markdown

    # 필수 섹션 확인
    assert "# 교통 시뮬레이션 분석 리포트" in markdown
    assert "## 1. 요약" in markdown
    assert "## 7. 정책적 해석" in markdown


@pytest.mark.asyncio
async def test_prompt_contains_kpis(reporter, analysis_result, mock_llm_gateway):
    """LLM 프롬프트에 KPI 포함 확인"""
    await reporter.generate_report(
        analysis_result=analysis_result,
    )

    call_args = mock_llm_gateway.generate.call_args[0][0]
    prompt = call_args.user_prompt

    # 주요 KPI가 프롬프트에 포함되었는지 확인
    assert "평균 통행 시간" in prompt or "average_travel_time" in prompt
    assert "Baseline" in prompt
    assert "Alternative" in prompt


@pytest.mark.asyncio
async def test_system_prompt_content(reporter, analysis_result, mock_llm_gateway):
    """시스템 프롬프트 내용 확인"""
    await reporter.generate_report(
        analysis_result=analysis_result,
    )

    call_args = mock_llm_gateway.generate.call_args[0][0]
    system_prompt = call_args.system_prompt

    assert "교통 정책 전문가" in system_prompt
    assert "정책적 관점" in system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
