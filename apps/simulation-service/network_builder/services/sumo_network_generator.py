"""
SUMO Network Generator

NetworkData를 SUMO .net.xml 형식으로 변환
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional

from ..providers.network_provider import NetworkData


class SumoNetworkGenerator:
    """
    SUMO 네트워크 XML 생성기

    NetworkData → .net.xml 변환
    """

    def generate_xml(self, network_data: NetworkData) -> str:
        """
        NetworkData를 SUMO .net.xml 형식으로 변환

        Args:
            network_data: 도로망 데이터

        Returns:
            .net.xml 문자열
        """
        # 루트 요소
        root = ET.Element("net", version="1.16", xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance")

        # Location (옵션)
        location = ET.SubElement(root, "location",
            netOffset="0.00,0.00",
            convBoundary="0.00,0.00,1000.00,1000.00",
            origBoundary="0.00,0.00,1000.00,1000.00",
            projParameter="!"
        )

        # 1. Edges (type definitions)
        edge_types = ET.SubElement(root, "type", id="default", priority="1", numLanes="2", speed="13.89")

        # 2. Nodes (junction)
        for node in network_data.nodes:
            node_elem = ET.SubElement(root, "junction",
                id=node["id"],
                type=node.get("type", "priority"),
                x=f"{node['x']:.2f}",
                y=f"{node['y']:.2f}",
                incLanes="",
                intLanes="",
                shape=""
            )

        # 3. Edges
        for edge in network_data.edges:
            edge_elem = ET.SubElement(root, "edge",
                id=edge["id"],
                **{"from": edge["from"]},
                to=edge["to"],
                priority=str(edge.get("priority", 1))
            )

            # Lanes
            for lane_idx in range(edge["lanes"]):
                lane_id = f"{edge['id']}_{lane_idx}"
                lane_elem = ET.SubElement(edge_elem, "lane",
                    id=lane_id,
                    index=str(lane_idx),
                    speed=f"{edge['speed']:.2f}",
                    length=f"{edge['length']:.2f}",
                    shape=f"0.00,{lane_idx * 3.2:.2f} {edge['length']:.2f},{lane_idx * 3.2:.2f}"
                )

        # 4. Connections
        for conn in network_data.connections:
            conn_elem = ET.SubElement(root, "connection",
                **{"from": conn["from"]},
                to=conn["to"],
                fromLane=str(conn["fromLane"]),
                toLane=str(conn["toLane"]),
                via="",
                dir="s",
                state="M"
            )

        # 5. Traffic Lights (선택적)
        if network_data.traffic_lights:
            for tl in network_data.traffic_lights:
                tl_elem = ET.SubElement(root, "tlLogic",
                    id=tl["id"],
                    type=tl.get("type", "static"),
                    programID=tl.get("programID", "0"),
                    offset=str(tl.get("offset", 0))
                )

                # Phases
                for phase in tl.get("phases", []):
                    phase_elem = ET.SubElement(tl_elem, "phase",
                        duration=str(phase["duration"]),
                        state=phase["state"]
                    )

        # XML 문자열로 변환 (pretty print)
        xml_str = self._prettify_xml(root)
        return xml_str

    def _prettify_xml(self, elem: ET.Element) -> str:
        """
        XML 요소를 보기 좋게 포맷팅

        Args:
            elem: XML 요소

        Returns:
            포맷팅된 XML 문자열
        """
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def calculate_statistics(self, network_data: NetworkData) -> dict:
        """
        도로망 통계 계산

        Args:
            network_data: 도로망 데이터

        Returns:
            통계 dict
        """
        total_length_m = sum(e.get("length", 0) for e in network_data.edges)
        avg_edge_length_m = total_length_m / len(network_data.edges) if network_data.edges else 0

        return {
            "nodes": len(network_data.nodes),
            "edges": len(network_data.edges),
            "junctions": len([n for n in network_data.nodes if n.get("type") != "dead_end"]),
            "traffic_lights": len(network_data.traffic_lights) if network_data.traffic_lights else 0,
            "total_length_km": total_length_m / 1000.0,
            "avg_edge_length_m": avg_edge_length_m,
        }
