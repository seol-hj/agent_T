"""
Route Generator

차량 경로를 SUMO .rou.xml 형식으로 변환
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional

from ..providers.demand_provider import DemandData, Trip


class RouteGenerator:
    """
    SUMO 경로 XML 생성기

    DemandData → .rou.xml 변환
    """

    def generate_xml(self, demand_data: DemandData) -> str:
        """
        DemandData를 SUMO .rou.xml 형식으로 변환

        Args:
            demand_data: 교통 수요 데이터

        Returns:
            .rou.xml 문자열
        """
        # 루트 요소
        root = ET.Element("routes", xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance")

        # 1. Vehicle Types
        for vtype_id, vtype_attrs in demand_data.vehicle_types.items():
            vtype_elem = ET.SubElement(root, "vType",
                id=vtype_id,
                vClass=vtype_attrs.get("vClass", "passenger"),
                length=f"{vtype_attrs.get('length', 5.0):.2f}",
                minGap=f"{vtype_attrs.get('minGap', 2.5):.2f}",
                maxSpeed=f"{vtype_attrs.get('maxSpeed', 30.0):.2f}",
                accel=f"{vtype_attrs.get('accel', 2.6):.2f}",
                decel=f"{vtype_attrs.get('decel', 4.5):.2f}",
                sigma=f"{vtype_attrs.get('sigma', 0.5):.2f}",
                color=vtype_attrs.get("color", "1,1,0"),
            )

        # 2. Vehicles (trips)
        for trip in sorted(demand_data.trips, key=lambda t: t.depart_time):
            if trip.route_edges:
                # 경로가 명시된 경우
                route_elem = ET.SubElement(root, "route",
                    id=f"route_{trip.vehicle_id}",
                    edges=" ".join(trip.route_edges)
                )
                vehicle_elem = ET.SubElement(root, "vehicle",
                    id=trip.vehicle_id,
                    type=trip.vehicle_type,
                    route=f"route_{trip.vehicle_id}",
                    depart=f"{trip.depart_time:.2f}"
                )
            else:
                # 출발지/목적지만 있는 경우 (SUMO가 경로 자동 계산)
                vehicle_elem = ET.SubElement(root, "trip",
                    id=trip.vehicle_id,
                    type=trip.vehicle_type,
                    depart=f"{trip.depart_time:.2f}",
                    **{"from": trip.from_edge},
                    to=trip.to_edge
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

    def calculate_statistics(self, demand_data: DemandData) -> dict:
        """
        교통 수요 통계 계산

        Args:
            demand_data: 교통 수요 데이터

        Returns:
            통계 dict
        """
        vehicle_type_counts = {}
        for trip in demand_data.trips:
            vtype = trip.vehicle_type
            vehicle_type_counts[vtype] = vehicle_type_counts.get(vtype, 0) + 1

        depart_times = [t.depart_time for t in demand_data.trips]
        avg_depart_time = sum(depart_times) / len(depart_times) if depart_times else 0

        return {
            "total_vehicles": len(demand_data.trips),
            "vehicles_by_type": vehicle_type_counts,
            "total_trips": len(demand_data.trips),
            "departure_time_range": [
                min(depart_times) if depart_times else 0,
                max(depart_times) if depart_times else 0,
            ],
            "avg_departure_time": avg_depart_time,
        }
