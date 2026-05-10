"""
SUMO Result Parser

SUMO 출력 XML 파일 파싱
"""

import xml.etree.ElementTree as ET
from typing import Optional
from dataclasses import dataclass


@dataclass
class TripInfo:
    """개별 차량 통행 정보"""
    vehicle_id: str
    depart_time: float
    arrival_time: float
    duration: float
    route_length: float
    waiting_time: float
    waiting_count: int
    time_loss: float
    vehicle_type: str
    speed_factor: float


@dataclass
class SummaryStep:
    """타임스텝별 요약 정보"""
    time: float
    loaded: int
    inserted: int
    running: int
    waiting: int
    ended: int
    mean_waiting_time: float
    mean_travel_time: float
    mean_speed: float
    mean_speed_relative: float
    halting: int


@dataclass
class QueueData:
    """엣지별 대기열 정보"""
    timestep: float
    edge_id: str
    queueing_time: float
    queueing_length: float
    queueing_length_ahead_of_traffic_light: float


@dataclass
class EmissionData:
    """차량별 배출량 정보"""
    timestep: float
    vehicle_id: str
    co2: float
    co: float
    hc: float
    nox: float
    pmx: float
    fuel: float


class SumoResultParser:
    """
    SUMO 결과 XML 파서

    tripinfo.xml, summary.xml, queue.xml, emission.xml 파싱
    """

    def parse_tripinfo(self, xml_content: str) -> list[TripInfo]:
        """
        tripinfo.xml 파싱

        Args:
            xml_content: tripinfo.xml 문자열

        Returns:
            TripInfo 리스트
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse tripinfo XML: {e}")

        trips = []

        for tripinfo_elem in root.findall("tripinfo"):
            try:
                trip = TripInfo(
                    vehicle_id=tripinfo_elem.get("id", ""),
                    depart_time=float(tripinfo_elem.get("depart", 0)),
                    arrival_time=float(tripinfo_elem.get("arrival", 0)),
                    duration=float(tripinfo_elem.get("duration", 0)),
                    route_length=float(tripinfo_elem.get("routeLength", 0)),
                    waiting_time=float(tripinfo_elem.get("waitingTime", 0)),
                    waiting_count=int(tripinfo_elem.get("waitingCount", 0)),
                    time_loss=float(tripinfo_elem.get("timeLoss", 0)),
                    vehicle_type=tripinfo_elem.get("vType", ""),
                    speed_factor=float(tripinfo_elem.get("speedFactor", 1.0)),
                )
                trips.append(trip)
            except (ValueError, TypeError) as e:
                # 개별 항목 파싱 실패 시 건너뜀
                continue

        return trips

    def parse_summary(self, xml_content: str) -> list[SummaryStep]:
        """
        summary.xml 파싱

        Args:
            xml_content: summary.xml 문자열

        Returns:
            SummaryStep 리스트
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse summary XML: {e}")

        steps = []

        for step_elem in root.findall("step"):
            try:
                step = SummaryStep(
                    time=float(step_elem.get("time", 0)),
                    loaded=int(step_elem.get("loaded", 0)),
                    inserted=int(step_elem.get("inserted", 0)),
                    running=int(step_elem.get("running", 0)),
                    waiting=int(step_elem.get("waiting", 0)),
                    ended=int(step_elem.get("ended", 0)),
                    mean_waiting_time=float(step_elem.get("meanWaitingTime", 0)),
                    mean_travel_time=float(step_elem.get("meanTravelTime", 0)),
                    mean_speed=float(step_elem.get("meanSpeed", 0)),
                    mean_speed_relative=float(step_elem.get("meanSpeedRelative", 0)),
                    halting=int(step_elem.get("halting", 0)),
                )
                steps.append(step)
            except (ValueError, TypeError) as e:
                continue

        return steps

    def parse_queue(self, xml_content: str) -> list[QueueData]:
        """
        queue.xml 파싱

        Args:
            xml_content: queue.xml 문자열

        Returns:
            QueueData 리스트
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse queue XML: {e}")

        queues = []

        for data_elem in root.findall("data"):
            timestep = float(data_elem.get("timestep", 0))

            for edge_elem in data_elem.findall("edge"):
                try:
                    queue = QueueData(
                        timestep=timestep,
                        edge_id=edge_elem.get("id", ""),
                        queueing_time=float(edge_elem.get("queueing_time", 0)),
                        queueing_length=float(edge_elem.get("queueing_length", 0)),
                        queueing_length_ahead_of_traffic_light=float(
                            edge_elem.get("queueing_length_ahead_of_traffic_light", 0)
                        ),
                    )
                    queues.append(queue)
                except (ValueError, TypeError) as e:
                    continue

        return queues

    def parse_emission(self, xml_content: str) -> list[EmissionData]:
        """
        emission.xml 파싱

        Args:
            xml_content: emission.xml 문자열

        Returns:
            EmissionData 리스트
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse emission XML: {e}")

        emissions = []

        for timestep_elem in root.findall("timestep"):
            timestep = float(timestep_elem.get("time", 0))

            for vehicle_elem in timestep_elem.findall("vehicle"):
                try:
                    emission = EmissionData(
                        timestep=timestep,
                        vehicle_id=vehicle_elem.get("id", ""),
                        co2=float(vehicle_elem.get("CO2", 0)),
                        co=float(vehicle_elem.get("CO", 0)),
                        hc=float(vehicle_elem.get("HC", 0)),
                        nox=float(vehicle_elem.get("NOx", 0)),
                        pmx=float(vehicle_elem.get("PMx", 0)),
                        fuel=float(vehicle_elem.get("fuel", 0)),
                    )
                    emissions.append(emission)
                except (ValueError, TypeError) as e:
                    continue

        return emissions
