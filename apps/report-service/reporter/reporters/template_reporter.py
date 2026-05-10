"""
Template Reporter

템플릿 기반 리포트 생성
"""

from datetime import datetime
from typing import Optional

from .reporter import Reporter, ReportContent


class TemplateReporter(Reporter):
    """
    템플릿 기반 리포터

    사전 정의된 Markdown 템플릿으로 리포트 생성
    """

    async def generate_report(
        self,
        analysis_result: dict,
        user_request: Optional[str] = None,
        experiment_context: Optional[dict] = None,
        rag_contexts: Optional[list] = None,
    ) -> ReportContent:
        """템플릿 기반 리포트 생성"""

        experiment_id = analysis_result.get("experiment_id", "N/A")
        kpi_comparison = analysis_result.get("kpi_comparison", {})
        overall_score = analysis_result.get("overall_score", 0.0)
        summary = analysis_result.get("summary", "")

        baseline_kpis = kpi_comparison.get("baseline_kpis", {})
        alternative_kpis = kpi_comparison.get("alternative_kpis", {})
        improvements = kpi_comparison.get("improvements", {})

        # Markdown 생성
        markdown = self._generate_markdown(
            experiment_id=experiment_id,
            user_request=user_request,
            baseline_kpis=baseline_kpis,
            alternative_kpis=alternative_kpis,
            improvements=improvements,
            overall_score=overall_score,
            summary=summary,
            experiment_context=experiment_context,
        )

        return ReportContent(markdown=markdown, pdf=None)

    def _generate_markdown(
        self,
        experiment_id: str,
        user_request: Optional[str],
        baseline_kpis: dict,
        alternative_kpis: dict,
        improvements: dict,
        overall_score: float,
        summary: str,
        experiment_context: Optional[dict],
    ) -> str:
        """Markdown 리포트 생성"""

        report = f"""# 교통 시뮬레이션 분석 리포트

**실험 ID**: {experiment_id}
**생성 일시**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

---

## 1. 요약

{summary}

**종합 평가 점수**: {overall_score:.2f}점

"""

        # 사용자 요청
        if user_request:
            report += f"""## 2. 사용자 요청

```
{user_request}
```

"""

        # 실험 조건
        if experiment_context:
            report += "## 3. 실험 조건\n\n"
            report += self._format_experiment_context(experiment_context)
            report += "\n"

        # 기준 시나리오 (Baseline)
        report += "## 4. 기준 시나리오 (Baseline) 결과\n\n"
        report += self._format_kpis_table(baseline_kpis)
        report += "\n"

        # 대안 시나리오 (Alternative)
        report += "## 5. 대안 시나리오 (Alternative) 결과\n\n"
        report += self._format_kpis_table(alternative_kpis)
        report += "\n"

        # 개선율
        report += "## 6. 개선율\n\n"
        report += self._format_improvements_table(improvements)
        report += "\n"

        # 정책적 해석
        report += """## 7. 정책적 해석

템플릿 기반 리포터는 정책적 해석을 제공하지 않습니다. LLM 기반 리포터를 사용하여 더 상세한 정책적 분석을 받으실 수 있습니다.

"""

        # 제한사항
        report += """## 8. 제한사항

- 본 분석은 시뮬레이션 결과를 기반으로 하며, 실제 도로 상황과 차이가 있을 수 있습니다.
- 교통량, 신호 타이밍 등의 입력 파라미터에 따라 결과가 달라질 수 있습니다.
- 장기적인 효과나 간접 영향은 고려되지 않았습니다.

"""

        # 후속 검토 사항
        report += """## 9. 후속 검토 사항

- 다양한 교통 수요 시나리오에서의 추가 검증
- 실제 현장 데이터와의 비교 분석
- 비용-편익 분석
- 이해관계자 의견 수렴

---

*본 리포트는 AI Agent T 플랫폼에서 자동 생성되었습니다.*
"""

        return report

    def _format_experiment_context(self, context: dict) -> str:
        """실험 컨텍스트 포맷팅"""
        lines = []
        for key, value in context.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)

    def _format_kpis_table(self, kpis: dict) -> str:
        """KPI 테이블 포맷팅"""
        if not kpis:
            return "*데이터 없음*\n"

        table = "| KPI | 값 | 단위 |\n"
        table += "|-----|------|------|\n"

        kpi_units = {
            "average_travel_time": "초",
            "average_waiting_time": "초",
            "average_speed": "m/s",
            "average_time_loss": "초",
            "average_queue_length": "m",
            "max_queue_length": "m",
            "completed_vehicle_count": "대",
            "total_route_length": "m",
            "total_co2": "mg",
            "total_co": "mg",
            "total_nox": "mg",
            "total_pmx": "mg",
            "total_fuel": "ml",
            "simulation_duration": "초",
            "total_vehicles_loaded": "대",
        }

        kpi_names = {
            "average_travel_time": "평균 통행 시간",
            "average_waiting_time": "평균 대기 시간",
            "average_speed": "평균 속도",
            "average_time_loss": "평균 시간 손실",
            "average_queue_length": "평균 대기열 길이",
            "max_queue_length": "최대 대기열 길이",
            "completed_vehicle_count": "완료 차량 수",
            "total_route_length": "총 주행 거리",
            "total_co2": "총 CO2 배출",
            "total_co": "총 CO 배출",
            "total_nox": "총 NOx 배출",
            "total_pmx": "총 미세먼지 배출",
            "total_fuel": "총 연료 소비",
            "simulation_duration": "시뮬레이션 시간",
            "total_vehicles_loaded": "로드된 차량 수",
        }

        for key, value in kpis.items():
            name = kpi_names.get(key, key)
            unit = kpi_units.get(key, "-")
            formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
            table += f"| {name} | {formatted_value} | {unit} |\n"

        return table

    def _format_improvements_table(self, improvements: dict) -> str:
        """개선율 테이블 포맷팅"""
        if not improvements:
            return "*데이터 없음*\n"

        table = "| KPI | 개선율 | 평가 |\n"
        table += "|-----|--------|------|\n"

        kpi_names = {
            "average_travel_time": "평균 통행 시간",
            "average_waiting_time": "평균 대기 시간",
            "average_speed": "평균 속도",
            "average_time_loss": "평균 시간 손실",
            "average_queue_length": "평균 대기열 길이",
            "max_queue_length": "최대 대기열 길이",
            "completed_vehicle_count": "완료 차량 수",
            "total_co2": "총 CO2 배출",
            "total_fuel": "총 연료 소비",
        }

        for key, value in improvements.items():
            if key not in kpi_names:
                continue

            name = kpi_names[key]
            formatted_value = f"{value:+.2f}%"

            if value > 5:
                evaluation = "✅ 우수"
            elif value > 0:
                evaluation = "✓ 개선"
            elif value > -5:
                evaluation = "→ 유사"
            else:
                evaluation = "❌ 악화"

            table += f"| {name} | {formatted_value} | {evaluation} |\n"

        return table
