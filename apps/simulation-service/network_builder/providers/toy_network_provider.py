"""
Toy Network Provider

테스트 및 데모용 간단한 도로망 생성
"""

import math
from typing import Optional
from .network_provider import NetworkProvider, NetworkData


class ToyNetworkProvider(NetworkProvider):
    """
    Toy 도로망 생성기

    간단한 그리드 형태의 도로망을 생성
    """

    def generate_network(
        self,
        source_config: dict,
        network_options: Optional[dict] = None,
    ) -> NetworkData:
        """
        그리드 도로망 생성

        Args:
            source_config: {"type": "toy", "grid_size": [rows, cols]}
            network_options: 네트워크 옵션

        Returns:
            NetworkData
        """
        grid_size = source_config.get("grid_size", [3, 3])
        rows, cols = grid_size

        spacing = 200.0  # 노드 간 거리 (미터)
        default_lanes = 2
        default_speed = 13.89  # 50 km/h → m/s

        # 옵션 파싱
        options = network_options or {}
        lanes = options.get("default_lanes", default_lanes)
        speed = options.get("default_speed", default_speed)

        # 1. 노드 생성
        nodes = []
        for r in range(rows):
            for c in range(cols):
                node_id = f"n_{r}_{c}"
                x = c * spacing
                y = r * spacing
                node_type = "traffic_light" if (r > 0 and r < rows - 1 and c > 0 and c < cols - 1) else "priority"
                nodes.append({
                    "id": node_id,
                    "x": x,
                    "y": y,
                    "type": node_type,
                })

        # 2. 엣지 생성 (수평 + 수직)
        edges = []
        edge_id = 0

        # 수평 엣지
        for r in range(rows):
            for c in range(cols - 1):
                from_node = f"n_{r}_{c}"
                to_node = f"n_{r}_{c+1}"

                # 양방향
                edges.append({
                    "id": f"e_{edge_id}",
                    "from": from_node,
                    "to": to_node,
                    "lanes": lanes,
                    "speed": speed,
                    "length": spacing,
                    "priority": 1,
                })
                edge_id += 1

                edges.append({
                    "id": f"e_{edge_id}",
                    "from": to_node,
                    "to": from_node,
                    "lanes": lanes,
                    "speed": speed,
                    "length": spacing,
                    "priority": 1,
                })
                edge_id += 1

        # 수직 엣지
        for r in range(rows - 1):
            for c in range(cols):
                from_node = f"n_{r}_{c}"
                to_node = f"n_{r+1}_{c}"

                # 양방향
                edges.append({
                    "id": f"e_{edge_id}",
                    "from": from_node,
                    "to": to_node,
                    "lanes": lanes,
                    "speed": speed,
                    "length": spacing,
                    "priority": 1,
                })
                edge_id += 1

                edges.append({
                    "id": f"e_{edge_id}",
                    "from": to_node,
                    "to": from_node,
                    "lanes": lanes,
                    "speed": speed,
                    "length": spacing,
                    "priority": 1,
                })
                edge_id += 1

        # 3. 연결 생성 (자동으로 모든 lane 연결)
        connections = []
        for edge in edges:
            from_node = edge["to"]  # edge의 목적지 노드가 연결의 시작점
            # 이 노드에서 출발하는 다른 엣지 찾기
            outgoing_edges = [e for e in edges if e["from"] == from_node and e["id"] != edge["id"]]

            for out_edge in outgoing_edges:
                # 모든 lane 연결
                for lane_idx in range(min(edge["lanes"], out_edge["lanes"])):
                    connections.append({
                        "from": edge["id"],
                        "to": out_edge["id"],
                        "fromLane": lane_idx,
                        "toLane": lane_idx,
                    })

        # 4. 신호등 생성 (내부 노드만)
        traffic_lights = []
        tl_id = 0
        for node in nodes:
            if node["type"] == "traffic_light":
                traffic_lights.append({
                    "id": f"tl_{tl_id}",
                    "junction": node["id"],
                    "type": "static",
                    "programID": "0",
                    "offset": 0,
                    "phases": [
                        {"duration": 31, "state": "GGrrrrGGrrrr"},  # 동서 녹색
                        {"duration": 6, "state": "yyrrrryyrrrr"},   # 동서 황색
                        {"duration": 31, "state": "rrGGrrrrGGrr"},  # 남북 녹색
                        {"duration": 6, "state": "rryyrrrryyrr"},   # 남북 황색
                    ],
                })
                tl_id += 1

        return NetworkData(
            nodes=nodes,
            edges=edges,
            connections=connections,
            traffic_lights=traffic_lights if options.get("tls_guess", True) else None,
        )

    def apply_modifications(
        self,
        network_data: NetworkData,
        modifications: list[dict],
    ) -> NetworkData:
        """
        도로망 수정사항 적용

        지원: lane_change, speed_change, traffic_light
        """
        modified_data = NetworkData(
            nodes=network_data.nodes.copy(),
            edges=[e.copy() for e in network_data.edges],
            connections=[c.copy() for c in network_data.connections],
            traffic_lights=[tl.copy() for tl in network_data.traffic_lights] if network_data.traffic_lights else None,
        )

        for mod in modifications:
            mod_type = mod.get("type")

            if mod_type == "lane_change":
                modified_data = self._apply_lane_change(modified_data, mod)
            elif mod_type == "speed_change":
                modified_data = self._apply_speed_change(modified_data, mod)
            elif mod_type == "traffic_light":
                modified_data = self._apply_traffic_light_change(modified_data, mod)

        return modified_data

    def _apply_lane_change(self, network_data: NetworkData, mod: dict) -> NetworkData:
        """
        차로 수 변경 적용

        strategy:
        - "increase_major_roads": 긴 엣지의 차로 증가
        - "increase_all": 모든 엣지의 차로 증가
        """
        lane_delta = mod.get("lane_delta", 1)
        strategy = mod.get("strategy", "increase_major_roads")

        if strategy == "increase_all":
            # 모든 엣지
            for edge in network_data.edges:
                edge["lanes"] = max(1, edge["lanes"] + lane_delta)

        elif strategy == "increase_major_roads":
            # 평균 길이 이상의 엣지만 (실제로는 모두 같지만 데모용)
            avg_length = sum(e["length"] for e in network_data.edges) / len(network_data.edges)
            for edge in network_data.edges:
                if edge["length"] >= avg_length:
                    edge["lanes"] = max(1, edge["lanes"] + lane_delta)

        # 연결 재생성 (lane 수 변경에 따라)
        # 간단하게: 모든 연결 삭제 후 재생성
        network_data.connections = []
        for edge in network_data.edges:
            from_node = edge["to"]
            outgoing_edges = [e for e in network_data.edges if e["from"] == from_node and e["id"] != edge["id"]]

            for out_edge in outgoing_edges:
                for lane_idx in range(min(edge["lanes"], out_edge["lanes"])):
                    network_data.connections.append({
                        "from": edge["id"],
                        "to": out_edge["id"],
                        "fromLane": lane_idx,
                        "toLane": lane_idx,
                    })

        return network_data

    def _apply_speed_change(self, network_data: NetworkData, mod: dict) -> NetworkData:
        """
        속도 제한 변경 적용

        strategy:
        - "increase_all": 모든 엣지의 속도 증가
        - "decrease_all": 모든 엣지의 속도 감소
        """
        speed_multiplier = mod.get("speed_multiplier", 1.1)
        strategy = mod.get("strategy", "increase_all")

        if strategy in ["increase_all", "decrease_all"]:
            for edge in network_data.edges:
                edge["speed"] = edge["speed"] * speed_multiplier

        return network_data

    def _apply_traffic_light_change(self, network_data: NetworkData, mod: dict) -> NetworkData:
        """
        신호등 타이밍 변경 적용 (placeholder)

        실제 구현에서는 SUMO TLS 프로그램 수정
        """
        cycle_seconds = mod.get("cycle_seconds", 90)
        green_time_ratio = mod.get("green_time_ratio", 0.55)

        if not network_data.traffic_lights:
            return network_data

        # 간단하게: 모든 신호등의 phase duration 조정
        green_time = int(cycle_seconds * green_time_ratio / 2)  # 2방향
        yellow_time = 3
        remaining = cycle_seconds - (green_time * 2 + yellow_time * 2)

        for tl in network_data.traffic_lights:
            tl["phases"] = [
                {"duration": green_time, "state": "GGrrrrGGrrrr"},
                {"duration": yellow_time, "state": "yyrrrryyrrrr"},
                {"duration": green_time + remaining, "state": "rrGGrrrrGGrr"},
                {"duration": yellow_time, "state": "rryyrrrryyrr"},
            ]

        return network_data
