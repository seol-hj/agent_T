"""
Network Provider Interface

도로망 생성을 위한 추상 인터페이스
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class NetworkData:
    """
    도로망 데이터

    SUMO .net.xml 생성에 필요한 노드, 엣지, 연결 정보
    """

    nodes: list[dict]  # 노드 목록 (id, x, y, type)
    edges: list[dict]  # 엣지 목록 (id, from, to, lanes, speed, length)
    connections: list[dict]  # 연결 목록 (from, to, fromLane, toLane)
    traffic_lights: Optional[list[dict]] = None  # 신호등 목록 (id, junctions)

    @property
    def statistics(self) -> dict:
        """도로망 통계"""
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "connections": len(self.connections),
            "traffic_lights": len(self.traffic_lights) if self.traffic_lights else 0,
            "total_length_km": sum(e.get("length", 0) for e in self.edges) / 1000.0,
        }


class NetworkProvider(ABC):
    """
    도로망 제공자 인터페이스

    다양한 소스(Toy, OSM)로부터 도로망 데이터를 생성
    """

    @abstractmethod
    def generate_network(
        self,
        source_config: dict,
        network_options: Optional[dict] = None,
    ) -> NetworkData:
        """
        도로망 데이터 생성

        Args:
            source_config: 소스 설정 (type, bbox, query 등)
            network_options: 네트워크 옵션 (vehicle_types, tls_guess 등)

        Returns:
            NetworkData
        """
        pass

    @abstractmethod
    def apply_modifications(
        self,
        network_data: NetworkData,
        modifications: list[dict],
    ) -> NetworkData:
        """
        도로망 수정사항 적용

        Args:
            network_data: 원본 도로망 데이터
            modifications: 수정사항 목록 (lane_change, speed_change, traffic_light 등)

        Returns:
            수정된 NetworkData
        """
        pass
