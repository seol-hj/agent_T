"""
Template Reporter Tests

TemplateReporter 단위 테스트
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from reporter.reporters.template_reporter import TemplateReporter


@pytest.fixture
def reporter():
    """TemplateReporter 인스턴스"""
    return TemplateReporter()


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
                "completed_vehicle_count": 100,
                "total_co2": 16590.0,
            },
            "alternative_kpis": {
                "average_travel_time": 110.0,
                "average_waiting_time": 9.6,
                "average_speed": 4.58,
                "completed_vehicle_count": 100,
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
async def test_generate_report_basic(reporter, analysis_result):
    """기본 리포트 생성 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    assert content.markdown is not None
    assert len(content.markdown) > 0
    assert content.pdf is None  # Template reporter는 PDF 미지원


@pytest.mark.asyncio
async def test_markdown_structure(reporter, analysis_result):
    """Markdown 구조 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    markdown = content.markdown

    # 필수 섹션 확인
    assert "# 교통 시뮬레이션 분석 리포트" in markdown
    assert "## 1. 요약" in markdown
    assert "## 4. 기준 시나리오 (Baseline) 결과" in markdown
    assert "## 5. 대안 시나리오 (Alternative) 결과" in markdown
    assert "## 6. 개선율" in markdown
    assert "## 7. 정책적 해석" in markdown
    assert "## 8. 제한사항" in markdown
    assert "## 9. 후속 검토 사항" in markdown


@pytest.mark.asyncio
async def test_markdown_with_user_request(reporter, analysis_result):
    """사용자 요청 포함 테스트"""
    user_request = "교통 수요를 20% 증가시켰을 때의 영향을 분석해주세요."

    content = await reporter.generate_report(
        analysis_result=analysis_result,
        user_request=user_request,
    )

    markdown = content.markdown
    assert "## 2. 사용자 요청" in markdown
    assert user_request in markdown


@pytest.mark.asyncio
async def test_markdown_with_experiment_context(reporter, analysis_result):
    """실험 컨텍스트 포함 테스트"""
    experiment_context = {
        "request_type": "demand_increase",
        "demand_multiplier": 1.2,
        "region": "서울시 강남구",
    }

    content = await reporter.generate_report(
        analysis_result=analysis_result,
        experiment_context=experiment_context,
    )

    markdown = content.markdown
    assert "## 3. 실험 조건" in markdown
    assert "demand_multiplier" in markdown
    assert "1.2" in markdown


@pytest.mark.asyncio
async def test_kpi_table_format(reporter, analysis_result):
    """KPI 테이블 포맷 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    markdown = content.markdown

    # 테이블 형식 확인
    assert "| KPI | 값 | 단위 |" in markdown
    assert "|-----|------|------|" in markdown

    # 주요 KPI 포함 확인
    assert "평균 통행 시간" in markdown
    assert "평균 대기 시간" in markdown
    assert "평균 속도" in markdown


@pytest.mark.asyncio
async def test_improvements_table_format(reporter, analysis_result):
    """개선율 테이블 포맷 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    markdown = content.markdown

    # 개선율 테이블 확인
    assert "| KPI | 개선율 | 평가 |" in markdown
    assert "+12.00%" in markdown  # 통행 시간 개선
    assert "✅" in markdown or "✓" in markdown  # 개선 마커


@pytest.mark.asyncio
async def test_empty_kpis(reporter):
    """빈 KPI 처리 테스트"""
    empty_result = {
        "experiment_id": "exp-empty",
        "kpi_comparison": {
            "baseline_kpis": {},
            "alternative_kpis": {},
            "improvements": {},
        },
        "overall_score": 0.0,
        "summary": "데이터 없음",
    }

    content = await reporter.generate_report(
        analysis_result=empty_result,
    )

    markdown = content.markdown
    assert "데이터 없음" in markdown


@pytest.mark.asyncio
async def test_overall_score_display(reporter, analysis_result):
    """종합 점수 표시 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    markdown = content.markdown
    assert "종합 평가 점수" in markdown
    assert "13.5" in markdown or "13.50" in markdown


@pytest.mark.asyncio
async def test_experiment_id_display(reporter, analysis_result):
    """실험 ID 표시 테스트"""
    content = await reporter.generate_report(
        analysis_result=analysis_result,
    )

    markdown = content.markdown
    assert "**실험 ID**: exp-001" in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
