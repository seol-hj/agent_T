"""
Demand Provider Interface

교통 수요 생성을 위한 추상 인터페이스
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Trip:
    """
    개별 통행

    차량의 출발지, 목적지, 출발 시간, 차종
    """

    vehicle_id: str
    from_edge: str
    to_edge: str
    depart_time: float  # 초
    vehicle_type: str
    route_edges: Optional[list[str]] = None  # 경로 (선택적)


@dataclass
class DemandData:
    """
    교통 수요 데이터

    SUMO .rou.xml 생성에 필요한 차량 통행 정보
    """

    trips: list[Trip]
    vehicle_types: dict[str, dict]  # 차종별 속성

    @property
    def statistics(self) -> dict:
        """수요 통계"""
        vehicle_type_counts = {}
        for trip in self.trips:
            vtype = trip.vehicle_type
            vehicle_type_counts[vtype] = vehicle_type_counts.get(vtype, 0) + 1

        return {
            "total_vehicles": len(self.trips),
            "vehicles_by_type": vehicle_type_counts,
            "total_trips": len(self.trips),
            "departure_time_range": [
                min(t.depart_time for t in self.trips) if self.trips else 0,
                max(t.depart_time for t in self.trips) if self.trips else 0,
            ],
        }


class DemandProvider(ABC):
    """
    교통 수요 제공자 인터페이스

    다양한 방법(Toy, OD Matrix)으로 교통 수요 생성
    """

    @abstractmethod
    def generate_demand(
        self,
        network_data: Any,
        demand_config: dict,
    ) -> DemandData:
        """
        교통 수요 생성

        Args:
            network_data: 도로망 데이터 (NetworkData)
            demand_config: 수요 설정 (vehicle_count, start_time, end_time 등)

        Returns:
            DemandData
        """
        pass

    @abstractmethod
    def apply_demand_multiplier(
        self,
        demand_data: DemandData,
        multiplier: float,
    ) -> DemandData:
        """
        수요 배율 적용

        Args:
            demand_data: 원본 수요 데이터
            multiplier: 배율 (1.2 = 20% 증가)

        Returns:
            조정된 DemandData
        """
        pass
