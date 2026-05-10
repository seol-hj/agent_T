"""
Toy Demand Provider

테스트 및 데모용 간단한 교통 수요 생성
"""

import random
from typing import Any, Optional
from .demand_provider import DemandProvider, DemandData, Trip


class ToyDemandProvider(DemandProvider):
    """
    Toy 교통 수요 생성기

    무작위 OD 쌍 및 출발 시간 생성
    """

    def __init__(self, random_seed: Optional[int] = None):
        """
        Args:
            random_seed: 랜덤 시드 (재현성)
        """
        self.random_seed = random_seed
        if random_seed is not None:
            random.seed(random_seed)

    def generate_demand(
        self,
        network_data: Any,
        demand_config: dict,
    ) -> DemandData:
        """
        교통 수요 생성

        Args:
            network_data: NetworkData (edges 사용)
            demand_config: {
                "vehicle_count": 차량 수,
                "start_time": 시작 시간 (초),
                "end_time": 종료 시간 (초),
                "vehicle_types": 차종 비율 dict,
                "trip_distribution": "random" | "uniform",
            }

        Returns:
            DemandData
        """
        vehicle_count = demand_config.get("vehicle_count", 100)
        start_time = demand_config.get("start_time", 0)
        end_time = demand_config.get("end_time", 3600)
        vehicle_types_ratio = demand_config.get("vehicle_types", {"passenger": 1.0})
        trip_distribution = demand_config.get("trip_distribution", "random")

        # 엣지 목록 (출발지/목적지 후보)
        edges = [e["id"] for e in network_data.edges] if hasattr(network_data, "edges") else []
        if not edges:
            raise ValueError("No edges available in network_data")

        # 차종 정의
        vehicle_type_defs = self._get_vehicle_type_definitions()

        # 차종별 차량 수 계산
        vehicle_type_assignments = self._assign_vehicle_types(
            vehicle_count, vehicle_types_ratio
        )

        # 통행 생성
        trips = []
        vehicle_id = 0

        for vtype, count in vehicle_type_assignments.items():
            for _ in range(count):
                # OD 선택 (무작위)
                from_edge = random.choice(edges)
                to_edge = random.choice([e for e in edges if e != from_edge])

                # 출발 시간 (균등 분포)
                if trip_distribution == "uniform":
                    depart_time = start_time + (end_time - start_time) * (vehicle_id / vehicle_count)
                else:  # random
                    depart_time = random.uniform(start_time, end_time)

                trips.append(Trip(
                    vehicle_id=f"veh_{vehicle_id}",
                    from_edge=from_edge,
                    to_edge=to_edge,
                    depart_time=depart_time,
                    vehicle_type=vtype,
                ))
                vehicle_id += 1

        return DemandData(
            trips=trips,
            vehicle_types=vehicle_type_defs,
        )

    def apply_demand_multiplier(
        self,
        demand_data: DemandData,
        multiplier: float,
    ) -> DemandData:
        """
        수요 배율 적용

        차량 수를 multiplier만큼 증가 (또는 감소)
        """
        if multiplier == 1.0:
            return demand_data

        original_count = len(demand_data.trips)
        target_count = int(original_count * multiplier)

        if multiplier > 1.0:
            # 증가: 기존 통행 복제
            new_trips = demand_data.trips.copy()
            additional_count = target_count - original_count

            for i in range(additional_count):
                # 기존 통행에서 무작위 선택하여 복제
                template = random.choice(demand_data.trips)
                new_trip = Trip(
                    vehicle_id=f"veh_{original_count + i}",
                    from_edge=template.from_edge,
                    to_edge=template.to_edge,
                    depart_time=template.depart_time + random.uniform(-10, 10),  # 약간의 시간 변동
                    vehicle_type=template.vehicle_type,
                    route_edges=template.route_edges,
                )
                new_trips.append(new_trip)

        else:
            # 감소: 무작위 샘플링
            new_trips = random.sample(demand_data.trips, target_count)

        return DemandData(
            trips=new_trips,
            vehicle_types=demand_data.vehicle_types,
        )

    def _assign_vehicle_types(
        self, vehicle_count: int, vehicle_types_ratio: dict[str, float]
    ) -> dict[str, int]:
        """
        차종별 차량 수 할당

        Args:
            vehicle_count: 총 차량 수
            vehicle_types_ratio: 차종 비율 (합이 1.0)

        Returns:
            차종별 차량 수 dict
        """
        # 비율 정규화
        total_ratio = sum(vehicle_types_ratio.values())
        normalized = {k: v / total_ratio for k, v in vehicle_types_ratio.items()}

        # 차량 수 할당
        assignments = {}
        assigned_total = 0

        for vtype, ratio in normalized.items():
            count = int(vehicle_count * ratio)
            assignments[vtype] = count
            assigned_total += count

        # 나머지를 첫 번째 타입에 추가
        if assigned_total < vehicle_count:
            first_type = list(normalized.keys())[0]
            assignments[first_type] += vehicle_count - assigned_total

        return assignments

    def _get_vehicle_type_definitions(self) -> dict[str, dict]:
        """
        차종 정의

        SUMO vType 속성
        """
        return {
            "passenger": {
                "vClass": "passenger",
                "length": 5.0,
                "minGap": 2.5,
                "maxSpeed": 30.0,  # m/s (~108 km/h)
                "accel": 2.6,
                "decel": 4.5,
                "sigma": 0.5,
                "color": "1,1,0",  # Yellow
            },
            "bus": {
                "vClass": "bus",
                "length": 12.0,
                "minGap": 2.5,
                "maxSpeed": 20.0,  # m/s (~72 km/h)
                "accel": 1.2,
                "decel": 3.5,
                "sigma": 0.5,
                "color": "0,1,1",  # Cyan
            },
            "truck": {
                "vClass": "truck",
                "length": 8.0,
                "minGap": 2.5,
                "maxSpeed": 25.0,  # m/s (~90 km/h)
                "accel": 1.5,
                "decel": 4.0,
                "sigma": 0.5,
                "color": "1,0,0",  # Red
            },
        }
