"""
SUMO Config Generator

.sumocfg 파일 생성
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional


class SumoConfigGenerator:
    """
    SUMO 설정 파일 (.sumocfg) 생성기

    SUMO 시뮬레이션 실행에 필요한 설정 파일 생성
    """

    def generate_config(
        self,
        network_file: str,
        route_file: str,
        output_files: dict[str, str],
        simulation_settings: Optional[dict] = None,
    ) -> str:
        """
        .sumocfg XML 생성

        Args:
            network_file: .net.xml 파일 경로 (상대 또는 절대)
            route_file: .rou.xml 파일 경로
            output_files: 출력 파일 경로 dict
                - tripinfo: tripinfo.xml
                - summary: summary.xml
                - queue: queue.xml
                - emission: emission.xml
            simulation_settings: 시뮬레이션 설정 (begin, end, step-length 등)

        Returns:
            .sumocfg XML 문자열
        """
        settings = simulation_settings or {}

        # 루트 요소
        root = ET.Element("configuration",
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance")

        # 1. Input
        input_elem = ET.SubElement(root, "input")
        ET.SubElement(input_elem, "net-file", value=network_file)
        ET.SubElement(input_elem, "route-files", value=route_file)

        # 2. Output
        output_elem = ET.SubElement(root, "output")
        if "tripinfo" in output_files:
            ET.SubElement(output_elem, "tripinfo-output", value=output_files["tripinfo"])
        if "summary" in output_files:
            ET.SubElement(output_elem, "summary-output", value=output_files["summary"])
        if "queue" in output_files:
            ET.SubElement(output_elem, "queue-output", value=output_files["queue"])
        if "emission" in output_files:
            ET.SubElement(output_elem, "emission-output", value=output_files["emission"])

        # 3. Time
        time_elem = ET.SubElement(root, "time")
        begin = settings.get("begin", 0)
        end = settings.get("end")
        step_length = settings.get("step_length", 1.0)

        ET.SubElement(time_elem, "begin", value=str(begin))
        if end is not None:
            ET.SubElement(time_elem, "end", value=str(end))
        ET.SubElement(time_elem, "step-length", value=str(step_length))

        # 4. Processing
        processing_elem = ET.SubElement(root, "processing")
        if settings.get("collision_action"):
            ET.SubElement(processing_elem, "collision.action",
                         value=settings["collision_action"])
        if settings.get("time_to_teleport"):
            ET.SubElement(processing_elem, "time-to-teleport",
                         value=str(settings["time_to_teleport"]))

        # 5. Report (옵션)
        report_elem = ET.SubElement(root, "report")
        ET.SubElement(report_elem, "verbose", value="true")
        ET.SubElement(report_elem, "no-step-log", value="false")

        # XML 문자열로 변환
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

    def generate_default_simulation_settings(
        self,
        begin: float = 0,
        end: Optional[float] = None,
        step_length: float = 1.0,
    ) -> dict:
        """
        기본 시뮬레이션 설정 생성

        Args:
            begin: 시작 시간 (초)
            end: 종료 시간 (초, None이면 모든 차량 완료까지)
            step_length: 타임스텝 길이 (초)

        Returns:
            설정 dict
        """
        settings = {
            "begin": begin,
            "step_length": step_length,
            "collision_action": "warn",
            "time_to_teleport": 300,  # 5분간 움직이지 않으면 텔레포트
        }

        if end is not None:
            settings["end"] = end

        return settings
