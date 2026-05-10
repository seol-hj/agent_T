"""
Scenario Comparator

Baseline과 Alternative 시나리오 비교
"""

from typing import Optional


class ScenarioComparator:
    """
    시나리오 비교기

    Baseline vs Alternative KPI 비교 및 개선율 계산
    """

    def compare_scenarios(
        self,
        baseline_kpis: dict,
        alternative_kpis: dict,
    ) -> dict:
        """
        시나리오 비교

        Args:
            baseline_kpis: Baseline KPI
            alternative_kpis: Alternative KPI

        Returns:
            비교 결과 dict (improvements, baseline, alternative)
        """
        improvements = self._calculate_improvements(baseline_kpis, alternative_kpis)

        comparison = {
            "baseline": baseline_kpis,
            "alternative": alternative_kpis,
            "improvements": improvements,
        }

        return comparison

    def _calculate_improvements(
        self,
        baseline_kpis: dict,
        alternative_kpis: dict,
    ) -> dict:
        """
        개선율 계산

        Args:
            baseline_kpis: Baseline KPI
            alternative_kpis: Alternative KPI

        Returns:
            개선율 dict (percentage)
        """
        improvements = {}

        # 감소가 좋은 지표 (음수가 개선)
        decrease_better = [
            "average_travel_time",
            "average_waiting_time",
            "average_queue_length",
            "max_queue_length",
            "average_time_loss",
            "total_co2",
            "total_co",
            "total_nox",
            "total_pmx",
            "total_fuel",
        ]

        # 증가가 좋은 지표 (양수가 개선)
        increase_better = [
            "average_speed",
            "completed_vehicle_count",
        ]

        for key in baseline_kpis:
            if key not in alternative_kpis:
                continue

            baseline_value = baseline_kpis[key]
            alternative_value = alternative_kpis[key]

            # 0으로 나누기 방지
            if baseline_value == 0:
                if alternative_value == 0:
                    improvement = 0.0
                else:
                    improvement = 100.0 if key in increase_better else -100.0
            else:
                # 변화율 계산
                change_rate = ((alternative_value - baseline_value) / baseline_value) * 100

                # 개선율 (감소가 좋은 지표는 부호 반전)
                if key in decrease_better:
                    improvement = -change_rate  # 감소하면 양수 개선
                elif key in increase_better:
                    improvement = change_rate   # 증가하면 양수 개선
                else:
                    improvement = change_rate   # 중립 지표

            improvements[key] = round(improvement, 2)

        return improvements

    def calculate_overall_score(self, improvements: dict) -> float:
        """
        종합 개선 점수 계산

        주요 지표에 가중치를 부여하여 종합 점수 산출

        Args:
            improvements: 개선율 dict

        Returns:
            종합 점수 (0-100, 높을수록 좋음)
        """
        # 가중치 정의
        weights = {
            "average_travel_time": 0.25,
            "average_waiting_time": 0.20,
            "average_speed": 0.15,
            "average_queue_length": 0.15,
            "total_co2": 0.15,
            "completed_vehicle_count": 0.10,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for key, weight in weights.items():
            if key in improvements:
                weighted_sum += improvements[key] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        # 정규화 (0-100 범위)
        score = weighted_sum / total_weight
        return round(score, 2)

    def generate_summary(self, comparison: dict) -> str:
        """
        비교 결과 요약 문장 생성

        Args:
            comparison: 비교 결과 dict

        Returns:
            요약 문자열
        """
        improvements = comparison["improvements"]

        # 주요 개선 지표
        major_improvements = []
        major_degradations = []

        key_metrics = [
            ("average_travel_time", "평균 통행 시간"),
            ("average_waiting_time", "평균 대기 시간"),
            ("average_speed", "평균 속도"),
            ("total_co2", "CO2 배출량"),
        ]

        for key, name in key_metrics:
            if key in improvements:
                value = improvements[key]
                if value > 5:
                    major_improvements.append(f"{name} {abs(value):.1f}% 개선")
                elif value < -5:
                    major_degradations.append(f"{name} {abs(value):.1f}% 악화")

        if major_improvements and not major_degradations:
            summary = f"Alternative 시나리오가 전반적으로 우수합니다. {', '.join(major_improvements)}."
        elif major_degradations and not major_improvements:
            summary = f"Alternative 시나리오가 일부 지표에서 악화되었습니다. {', '.join(major_degradations)}."
        elif major_improvements and major_degradations:
            summary = f"Alternative 시나리오는 일부 개선과 악화를 보입니다. 개선: {', '.join(major_improvements)}. 악화: {', '.join(major_degradations)}."
        else:
            summary = "Alternative 시나리오와 Baseline 시나리오의 성능 차이가 크지 않습니다."

        return summary
