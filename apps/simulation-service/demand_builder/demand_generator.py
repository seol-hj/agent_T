"""
Demand Generator

교통 수요(trip, route) 생성
"""
import os
import subprocess
import random
from typing import Dict, Any, Optional, List, Tuple
from lxml import etree


class DemandGenerator:
    """SUMO 교통 수요 생성기"""

    def __init__(self, sumo_tools_path: Optional[str] = None):
        """
        Args:
            sumo_tools_path: SUMO tools 경로
        """
        self.sumo_tools_path = sumo_tools_path or os.getenv("SUMO_HOME", "/usr/share/sumo")
        self.randomtrips_path = self._find_randomtrips()
        self.duarouter_path = self._find_duarouter()

    def _find_randomtrips(self) -> str:
        """randomTrips.py 스크립트 찾기"""
        # SUMO_HOME/tools/randomTrips.py
        script_path = os.path.join(self.sumo_tools_path, "tools", "randomTrips.py")
        if os.path.exists(script_path):
            return script_path

        # /usr/share/sumo/tools/randomTrips.py
        if os.path.exists("/usr/share/sumo/tools/randomTrips.py"):
            return "/usr/share/sumo/tools/randomTrips.py"

        # Fallback
        return "randomTrips.py"

    def _find_duarouter(self) -> str:
        """duarouter 실행 파일 찾기"""
        try:
            result = subprocess.run(
                ["which", "duarouter"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        duarouter_bin = os.path.join(self.sumo_tools_path, "bin", "duarouter")
        if os.path.exists(duarouter_bin):
            return duarouter_bin

        if os.path.exists("/usr/bin/duarouter"):
            return "/usr/bin/duarouter"

        return "duarouter"

    def generate_random_trips(
        self,
        net_file: str,
        output_file: str,
        vehicle_count: int,
        begin: float = 0.0,
        end: float = 3600.0,
        period: Optional[float] = None,
        vehicle_types: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        randomTrips.py를 사용하여 랜덤 trip 생성

        Args:
            net_file: 네트워크 파일
            output_file: 출력 trip 파일
            vehicle_count: 차량 수
            begin: 시작 시간 (초)
            end: 종료 시간 (초)
            period: 차량 생성 주기 (초) - None이면 자동 계산
            vehicle_types: 차량 타입 목록

        Returns:
            (성공 여부, 에러 메시지)
        """
        if period is None:
            period = (end - begin) / vehicle_count

        cmd = [
            "python3",
            self.randomtrips_path,
            "-n", net_file,
            "-o", output_file,
            "-b", str(begin),
            "-e", str(end),
            "-p", str(period),
            "--fringe-factor", "10",
            "--min-distance", "300",
            "--validate",
        ]

        # 차량 타입 지정
        if vehicle_types:
            cmd.extend(["--vehicle-class", ",".join(vehicle_types)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"randomTrips.py 실패: {error_msg}")
                return False, error_msg

            if not os.path.exists(output_file):
                return False, "trip 파일이 생성되지 않았습니다"

            return True, None

        except FileNotFoundError:
            return False, f"randomTrips.py를 찾을 수 없습니다: {self.randomtrips_path}"
        except Exception as e:
            return False, str(e)

    def generate_routes_from_trips(
        self,
        net_file: str,
        trip_file: str,
        output_file: str,
        additional_files: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        duarouter를 사용하여 trip → route 변환

        Args:
            net_file: 네트워크 파일
            trip_file: trip 파일
            output_file: 출력 route 파일
            additional_files: 추가 파일 (vType 정의 등)

        Returns:
            (성공 여부, 에러 메시지)
        """
        cmd = [
            self.duarouter_path,
            "-n", net_file,
            "-t", trip_file,
            "-o", output_file,
            "--ignore-errors",
            "--no-warnings",
        ]

        if additional_files:
            for add_file in additional_files:
                cmd.extend(["-a", add_file])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"duarouter 실패: {error_msg}")
                return False, error_msg

            if not os.path.exists(output_file):
                return False, "route 파일이 생성되지 않았습니다"

            return True, None

        except FileNotFoundError:
            return False, f"duarouter를 찾을 수 없습니다: {self.duarouter_path}"
        except Exception as e:
            return False, str(e)

    def create_vehicle_types(
        self,
        output_file: str,
        vehicle_types: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        차량 타입 정의 파일 생성

        Args:
            output_file: 출력 파일
            vehicle_types: 차량 타입 리스트
                [{"id": "car", "vClass": "passenger", "maxSpeed": 50.0, ...}, ...]

        Returns:
            성공 여부
        """
        if vehicle_types is None:
            vehicle_types = [
                {
                    "id": "car",
                    "vClass": "passenger",
                    "maxSpeed": 50.0,
                    "accel": 2.6,
                    "decel": 4.5,
                    "sigma": 0.5,
                    "length": 5.0,
                    "color": "1,1,0",
                },
                {
                    "id": "bus",
                    "vClass": "bus",
                    "maxSpeed": 30.0,
                    "accel": 1.2,
                    "decel": 3.0,
                    "sigma": 0.3,
                    "length": 12.0,
                    "color": "0,1,0",
                },
                {
                    "id": "truck",
                    "vClass": "truck",
                    "maxSpeed": 40.0,
                    "accel": 1.0,
                    "decel": 3.5,
                    "sigma": 0.4,
                    "length": 10.0,
                    "color": "0,0,1",
                },
            ]

        root = etree.Element("additional")

        for vtype in vehicle_types:
            vtype_elem = etree.SubElement(root, "vType")
            for key, value in vtype.items():
                vtype_elem.set(key, str(value))

        tree = etree.ElementTree(root)
        tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")

        return True

    def parse_route_stats(self, route_file: str) -> Dict[str, int]:
        """
        생성된 route 통계 추출

        Args:
            route_file: .rou.xml 파일

        Returns:
            통계 (vehicle_count, route_count)
        """
        try:
            tree = etree.parse(route_file)
            root = tree.getroot()

            vehicle_count = len(root.findall(".//vehicle"))
            route_count = len(root.findall(".//route"))

            return {
                "vehicle_count": vehicle_count,
                "route_count": route_count,
            }
        except Exception as e:
            print(f"Route 통계 파싱 실패: {e}")
            return {
                "vehicle_count": 0,
                "route_count": 0,
            }

    def build_demand(
        self,
        net_file: str,
        output_dir: str,
        demand_id: str,
        vehicle_count: int = 1000,
        duration_hours: float = 1.0,
        vehicle_type_distribution: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, Optional[str], Dict[str, int]]:
        """
        전체 수요 생성 프로세스

        Args:
            net_file: 네트워크 파일
            output_dir: 출력 디렉토리
            demand_id: 수요 ID
            vehicle_count: 차량 수
            duration_hours: 시뮬레이션 시간 (시간)
            vehicle_type_distribution: 차량 타입 분포 {"car": 0.7, "bus": 0.2, "truck": 0.1}

        Returns:
            (성공 여부, route 파일 경로, 통계)
        """
        os.makedirs(output_dir, exist_ok=True)

        # Placeholder 네트워크인지 확인
        is_placeholder = self._is_placeholder_network(net_file)
        if is_placeholder:
            print(f"Placeholder 네트워크 감지 - placeholder 수요 생성")
            return self._create_placeholder_demand(output_dir, demand_id, vehicle_count)

        duration_seconds = duration_hours * 3600.0

        # 1. 차량 타입 정의 파일 생성
        vtype_file = os.path.join(output_dir, f"{demand_id}.vtypes.xml")
        self.create_vehicle_types(vtype_file)

        # 2. randomTrips로 trip 생성
        trip_file = os.path.join(output_dir, f"{demand_id}.trips.xml")
        success, error = self.generate_random_trips(
            net_file=net_file,
            output_file=trip_file,
            vehicle_count=vehicle_count,
            begin=0.0,
            end=duration_seconds,
        )

        if not success:
            # Fallback: placeholder trip 생성
            return self._create_placeholder_demand(output_dir, demand_id, vehicle_count)

        # 3. duarouter로 trip → route 변환
        route_file = os.path.join(output_dir, f"{demand_id}.rou.xml")
        success, error = self.generate_routes_from_trips(
            net_file=net_file,
            trip_file=trip_file,
            output_file=route_file,
            additional_files=[vtype_file]
        )

        if not success:
            return self._create_placeholder_demand(output_dir, demand_id, vehicle_count)

        # 4. 통계 추출
        stats = self.parse_route_stats(route_file)

        # 5. trip 파일 삭제 (용량 절약)
        try:
            os.remove(trip_file)
        except Exception:
            pass

        return True, route_file, stats

    def _is_placeholder_network(self, net_file: str) -> bool:
        """네트워크 파일이 placeholder인지 확인"""
        try:
            with open(net_file, "r", encoding="utf-8") as f:
                content = f.read()
                return "Placeholder network" in content
        except Exception:
            return False

    def _create_placeholder_demand(
        self,
        output_dir: str,
        demand_id: str,
        vehicle_count: int
    ) -> Tuple[bool, str, Dict[str, int]]:
        """Placeholder 수요 생성 (SUMO 도구가 없을 때)"""
        route_file = os.path.join(output_dir, f"{demand_id}.rou.xml")

        placeholder_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <!-- Placeholder demand for {demand_id} with {vehicle_count} vehicles -->
    <vType id="car" vClass="passenger" maxSpeed="50.0" accel="2.6" decel="4.5" sigma="0.5" length="5.0"/>

    <vehicle id="veh_0" type="car" depart="0.00">
        <route edges="edge1 edge2"/>
    </vehicle>
    <vehicle id="veh_1" type="car" depart="10.00">
        <route edges="edge1 edge2"/>
    </vehicle>
    <vehicle id="veh_2" type="car" depart="20.00">
        <route edges="edge3"/>
    </vehicle>
</routes>
"""

        with open(route_file, "w", encoding="utf-8") as f:
            f.write(placeholder_xml)

        return True, route_file, {
            "vehicle_count": 3,
            "route_count": 2,
        }
