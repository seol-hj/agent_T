"""
KPI Engine

SUMO 결과로부터 KPI 계산
"""

from typing import Optional
from ..parsers.sumo_result_parser import (
    TripInfo,
    SummaryStep,
    QueueData,
    EmissionData,
)


class KPIEngine:
    """
    KPI 계산 엔진

    SUMO 파싱 결과로부터 주요 KPI 추출
    """

    def calculate_kpis(
        self,
        trips: list[TripInfo],
        summary_steps: list[SummaryStep],
        queues: list[QueueData],
        emissions: list[EmissionData],
    ) -> dict:
        """
        전체 KPI 계산

        Args:
            trips: tripinfo 파싱 결과
            summary_steps: summary 파싱 결과
            queues: queue 파싱 결과
            emissions: emission 파싱 결과

        Returns:
            KPI dict
        """
        kpis = {}

        # Trip 기반 KPI
        if trips:
            kpis["average_travel_time"] = self._calculate_average_travel_time(trips)
            kpis["average_waiting_time"] = self._calculate_average_waiting_time(trips)
            kpis["average_speed"] = self._calculate_average_speed(trips)
            kpis["completed_vehicle_count"] = len(trips)
            kpis["total_route_length"] = sum(t.route_length for t in trips)
            kpis["average_time_loss"] = self._calculate_average_time_loss(trips)
        else:
            kpis["average_travel_time"] = 0.0
            kpis["average_waiting_time"] = 0.0
            kpis["average_speed"] = 0.0
            kpis["completed_vehicle_count"] = 0
            kpis["total_route_length"] = 0.0
            kpis["average_time_loss"] = 0.0

        # Queue 기반 KPI
        if queues:
            kpis["average_queue_length"] = self._calculate_average_queue_length(queues)
            kpis["max_queue_length"] = self._calculate_max_queue_length(queues)
        else:
            kpis["average_queue_length"] = 0.0
            kpis["max_queue_length"] = 0.0

        # Emission 기반 KPI
        if emissions:
            kpis["total_co2"] = self._calculate_total_co2(emissions)
            kpis["total_co"] = self._calculate_total_co(emissions)
            kpis["total_nox"] = self._calculate_total_nox(emissions)
            kpis["total_pmx"] = self._calculate_total_pmx(emissions)
            kpis["total_fuel"] = self._calculate_total_fuel(emissions)
        else:
            kpis["total_co2"] = 0.0
            kpis["total_co"] = 0.0
            kpis["total_nox"] = 0.0
            kpis["total_pmx"] = 0.0
            kpis["total_fuel"] = 0.0

        # Summary 기반 KPI (추가)
        if summary_steps:
            kpis["simulation_duration"] = self._calculate_simulation_duration(summary_steps)
            kpis["total_vehicles_loaded"] = self._calculate_total_loaded(summary_steps)
        else:
            kpis["simulation_duration"] = 0.0
            kpis["total_vehicles_loaded"] = 0

        return kpis

    def _calculate_average_travel_time(self, trips: list[TripInfo]) -> float:
        """평균 통행 시간 (초)"""
        if not trips:
            return 0.0
        return sum(t.duration for t in trips) / len(trips)

    def _calculate_average_waiting_time(self, trips: list[TripInfo]) -> float:
        """평균 대기 시간 (초)"""
        if not trips:
            return 0.0
        return sum(t.waiting_time for t in trips) / len(trips)

    def _calculate_average_speed(self, trips: list[TripInfo]) -> float:
        """평균 속도 (m/s)"""
        if not trips:
            return 0.0

        # 속도 = 거리 / 시간
        total_distance = sum(t.route_length for t in trips)
        total_time = sum(t.duration for t in trips)

        if total_time == 0:
            return 0.0

        return total_distance / total_time

    def _calculate_average_time_loss(self, trips: list[TripInfo]) -> float:
        """평균 시간 손실 (초)"""
        if not trips:
            return 0.0
        return sum(t.time_loss for t in trips) / len(trips)

    def _calculate_average_queue_length(self, queues: list[QueueData]) -> float:
        """평균 대기열 길이 (m)"""
        if not queues:
            return 0.0
        return sum(q.queueing_length for q in queues) / len(queues)

    def _calculate_max_queue_length(self, queues: list[QueueData]) -> float:
        """최대 대기열 길이 (m)"""
        if not queues:
            return 0.0
        return max(q.queueing_length for q in queues)

    def _calculate_total_co2(self, emissions: list[EmissionData]) -> float:
        """총 CO2 배출량 (mg)"""
        return sum(e.co2 for e in emissions)

    def _calculate_total_co(self, emissions: list[EmissionData]) -> float:
        """총 CO 배출량 (mg)"""
        return sum(e.co for e in emissions)

    def _calculate_total_nox(self, emissions: list[EmissionData]) -> float:
        """총 NOx 배출량 (mg)"""
        return sum(e.nox for e in emissions)

    def _calculate_total_pmx(self, emissions: list[EmissionData]) -> float:
        """총 PMx 배출량 (mg)"""
        return sum(e.pmx for e in emissions)

    def _calculate_total_fuel(self, emissions: list[EmissionData]) -> float:
        """총 연료 소비 (ml)"""
        return sum(e.fuel for e in emissions)

    def _calculate_simulation_duration(self, summary_steps: list[SummaryStep]) -> float:
        """시뮬레이션 총 시간 (초)"""
        if not summary_steps:
            return 0.0
        return max(step.time for step in summary_steps)

    def _calculate_total_loaded(self, summary_steps: list[SummaryStep]) -> int:
        """로드된 총 차량 수"""
        if not summary_steps:
            return 0
        return max(step.loaded for step in summary_steps)
