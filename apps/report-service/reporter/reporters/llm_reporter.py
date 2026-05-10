"""
LLM Reporter

LLM 기반 정책적 해석 리포트 생성
"""

from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.gateways.llm import LLMGateway, LLMRequest

from .reporter import Reporter, ReportContent


class LLMReporter(Reporter):
    """
    LLM 기반 리포터

    LLMGateway를 사용하여 정책적 해석 생성
    """

    def __init__(self, llm_gateway: LLMGateway):
        """
        Args:
            llm_gateway: LLM Gateway
        """
        self.llm = llm_gateway

    async def generate_report(
        self,
        analysis_result: dict,
        user_request: Optional[str] = None,
        experiment_context: Optional[dict] = None,
        rag_contexts: Optional[list] = None,
    ) -> ReportContent:
        """LLM 기반 리포트 생성"""

        experiment_id = analysis_result.get("experiment_id", "N/A")
        kpi_comparison = analysis_result.get("kpi_comparison", {})
        overall_score = analysis_result.get("overall_score", 0.0)
        summary = analysis_result.get("summary", "")

        baseline_kpis = kpi_comparison.get("baseline_kpis", {})
        alternative_kpis = kpi_comparison.get("alternative_kpis", {})
        improvements = kpi_comparison.get("improvements", {})

        # LLM으로 정책적 해석 생성
        policy_interpretation = await self._generate_policy_interpretation(
            user_request=user_request,
            baseline_kpis=baseline_kpis,
            alternative_kpis=alternative_kpis,
            improvements=improvements,
            overall_score=overall_score,
            summary=summary,
            rag_contexts=rag_contexts,
        )

        # Markdown 생성
        markdown = self._generate_markdown(
            experiment_id=experiment_id,
            user_request=user_request,
            baseline_kpis=baseline_kpis,
            alternative_kpis=alternative_kpis,
            improvements=improvements,
            overall_score=overall_score,
            summary=summary,
            policy_interpretation=policy_interpretation,
            experiment_context=experiment_context,
        )

        return ReportContent(markdown=markdown, pdf=None)

    async def _generate_policy_interpretation(
        self,
        user_request: Optional[str],
        baseline_kpis: dict,
        alternative_kpis: dict,
        improvements: dict,
        overall_score: float,
        summary: str,
        rag_contexts: Optional[list],
    ) -> str:
        """LLM을 사용한 정책적 해석 생성"""

        # 프롬프트 생성
        prompt = self._build_interpretation_prompt(
            user_request=user_request,
            baseline_kpis=baseline_kpis,
            alternative_kpis=alternative_kpis,
            improvements=improvements,
            overall_score=overall_score,
            summary=summary,
            rag_contexts=rag_contexts,
        )

        # LLM 호출
        llm_request = LLMRequest(
            system_prompt=self._get_system_prompt(),
            user_prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )

        response = await self.llm.generate(llm_request)

        return response.content

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 교통 정책 전문가입니다.
교통 시뮬레이션 분석 결과를 바탕으로 정책적 관점에서 해석하고 권고사항을 제시합니다.

다음 관점에서 분석하세요:
1. 교통 효율성 (통행 시간, 속도, 대기 시간)
2. 환경 영향 (배출량, 연료 소비)
3. 교통 안전 및 편의성
4. 실행 가능성 및 비용 효과

답변은 정책 입안자가 이해하기 쉽도록 명확하고 구체적으로 작성하세요."""

    def _build_interpretation_prompt(
        self,
        user_request: Optional[str],
        baseline_kpis: dict,
        alternative_kpis: dict,
        improvements: dict,
        overall_score: float,
        summary: str,
        rag_contexts: Optional[list],
    ) -> str:
        """해석 프롬프트 생성"""

        prompt = "# 교통 시뮬레이션 분석 결과\n\n"

        # 사용자 요청
        if user_request:
            prompt += f"## 사용자 요청\n{user_request}\n\n"

        # 요약
        prompt += f"## 분석 요약\n{summary}\n\n"
        prompt += f"**종합 평가 점수**: {overall_score:.2f}점\n\n"

        # 주요 KPI
        prompt += "## 주요 KPI 비교\n\n"
        prompt += "| KPI | Baseline | Alternative | 개선율 |\n"
        prompt += "|-----|----------|-------------|--------|\n"

        key_kpis = [
            ("average_travel_time", "평균 통행 시간"),
            ("average_waiting_time", "평균 대기 시간"),
            ("average_speed", "평균 속도"),
            ("average_queue_length", "평균 대기열"),
            ("total_co2", "총 CO2"),
        ]

        for key, name in key_kpis:
            baseline = baseline_kpis.get(key, 0)
            alternative = alternative_kpis.get(key, 0)
            improvement = improvements.get(key, 0)
            prompt += f"| {name} | {baseline:.2f} | {alternative:.2f} | {improvement:+.2f}% |\n"

        prompt += "\n"

        # RAG 컨텍스트
        if rag_contexts:
            prompt += "## 참고 자료\n\n"
            for ctx in rag_contexts:
                prompt += f"- {ctx.get('content', '')}\n"
            prompt += "\n"

        # 요청
        prompt += """## 요청사항

위 분석 결과를 바탕으로 다음 내용을 작성하세요:

1. **정책적 해석** (2-3 문단)
   - 주요 개선/악화 지표의 의미
   - 교통 효율성 및 환경 영향
   - 실제 정책 적용 시 기대 효과

2. **권고사항** (3-5개 bullet points)
   - 구체적이고 실행 가능한 제안
   - 우선순위 및 단계별 접근

3. **주의사항** (2-3개 bullet points)
   - 시뮬레이션의 한계
   - 추가 검토가 필요한 사항

Markdown 형식으로 작성하세요."""

        return prompt

    def _generate_markdown(
        self,
        experiment_id: str,
        user_request: Optional[str],
        baseline_kpis: dict,
        alternative_kpis: dict,
        improvements: dict,
        overall_score: float,
        summary: str,
        policy_interpretation: str,
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

        # 기준 시나리오
        report += "## 4. 기준 시나리오 (Baseline) 결과\n\n"
        report += self._format_kpis_table(baseline_kpis)
        report += "\n"

        # 대안 시나리오
        report += "## 5. 대안 시나리오 (Alternative) 결과\n\n"
        report += self._format_kpis_table(alternative_kpis)
        report += "\n"

        # 개선율
        report += "## 6. 개선율\n\n"
        report += self._format_improvements_table(improvements)
        report += "\n"

        # 정책적 해석 (LLM 생성)
        report += f"""## 7. 정책적 해석

{policy_interpretation}

"""

        # 제한사항
        report += """## 8. 제한사항

- 본 분석은 시뮬레이션 결과를 기반으로 하며, 실제 도로 상황과 차이가 있을 수 있습니다.
- 교통량, 신호 타이밍 등의 입력 파라미터에 따라 결과가 달라질 수 있습니다.
- 장기적인 효과나 간접 영향은 고려되지 않았습니다.
- 비용-편익 분석은 포함되지 않았습니다.

"""

        # 후속 검토 사항
        report += """## 9. 후속 검토 사항

- 다양한 교통 수요 시나리오에서의 추가 검증
- 실제 현장 데이터와의 비교 분석
- 비용-편익 분석 및 예산 검토
- 이해관계자 의견 수렴 및 공청회
- 단계적 시범 적용 계획 수립

---

*본 리포트는 AI Agent T 플랫폼에서 LLM 기반으로 자동 생성되었습니다.*
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
            "average_queue_length": "m",
            "completed_vehicle_count": "대",
            "total_co2": "mg",
            "total_fuel": "ml",
        }

        kpi_names = {
            "average_travel_time": "평균 통행 시간",
            "average_waiting_time": "평균 대기 시간",
            "average_speed": "평균 속도",
            "average_queue_length": "평균 대기열 길이",
            "completed_vehicle_count": "완료 차량 수",
            "total_co2": "총 CO2 배출",
            "total_fuel": "총 연료 소비",
        }

        for key in ["average_travel_time", "average_waiting_time", "average_speed", "average_queue_length", "completed_vehicle_count", "total_co2", "total_fuel"]:
            if key in kpis:
                name = kpi_names[key]
                value = kpis[key]
                unit = kpi_units[key]
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
            "average_queue_length": "평균 대기열 길이",
            "total_co2": "총 CO2 배출",
            "total_fuel": "총 연료 소비",
        }

        for key in ["average_travel_time", "average_waiting_time", "average_speed", "average_queue_length", "total_co2", "total_fuel"]:
            if key not in improvements:
                continue

            name = kpi_names[key]
            value = improvements[key]
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
