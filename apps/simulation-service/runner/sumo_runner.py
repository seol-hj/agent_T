"""
SUMO Runner

SUMO 시뮬레이션 실행 및 결과 수집
"""
import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from lxml import etree


class SUMORunner:
    """SUMO 시뮬레이션 실행기"""

    def __init__(self, sumo_binary: Optional[str] = None):
        """
        Args:
            sumo_binary: SUMO 실행 파일 경로 (기본: sumo-gui 또는 sumo)
        """
        self.sumo_binary = sumo_binary or self._find_sumo()

    def _find_sumo(self) -> str:
        """SUMO 실행 파일 찾기"""
        # 1. 환경변수 확인
        if "SUMO_BINARY" in os.environ:
            return os.environ["SUMO_BINARY"]

        # 2. sumo 명령어 (GUI 없는 버전, 서버용)
        try:
            result = subprocess.run(
                ["which", "sumo"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # 3. SUMO_HOME/bin/sumo
        sumo_home = os.getenv("SUMO_HOME", "/usr/share/sumo")
        sumo_bin = os.path.join(sumo_home, "bin", "sumo")
        if os.path.exists(sumo_bin):
            return sumo_bin

        # 4. /usr/bin/sumo
        if os.path.exists("/usr/bin/sumo"):
            return "/usr/bin/sumo"

        # Fallback
        return "sumo"

    def create_sumocfg(
        self,
        net_file: str,
        route_file: str,
        output_dir: str,
        config_name: str,
        begin: float = 0.0,
        end: float = 3600.0,
        step_length: float = 1.0,
        additional_files: Optional[List[str]] = None
    ) -> str:
        """
        SUMO 설정 파일(.sumocfg) 생성

        Args:
            net_file: 네트워크 파일
            route_file: 경로 파일
            output_dir: 출력 디렉토리
            config_name: 설정 파일 이름
            begin: 시작 시간
            end: 종료 시간
            step_length: 시뮬레이션 스텝 길이 (초)
            additional_files: 추가 파일 목록

        Returns:
            생성된 .sumocfg 파일 경로
        """
        config_path = os.path.join(output_dir, f"{config_name}.sumocfg")

        root = etree.Element("configuration")

        # Input 섹션
        input_elem = etree.SubElement(root, "input")
        etree.SubElement(input_elem, "net-file", value=net_file)
        etree.SubElement(input_elem, "route-files", value=route_file)
        if additional_files:
            etree.SubElement(input_elem, "additional-files", value=",".join(additional_files))

        # Time 섹션
        time_elem = etree.SubElement(root, "time")
        etree.SubElement(time_elem, "begin", value=str(begin))
        etree.SubElement(time_elem, "end", value=str(end))
        etree.SubElement(time_elem, "step-length", value=str(step_length))

        # Output 섹션
        output_elem = etree.SubElement(root, "output")
        tripinfo_file = os.path.join(output_dir, f"{config_name}.tripinfo.xml")
        summary_file = os.path.join(output_dir, f"{config_name}.summary.xml")
        etree.SubElement(output_elem, "tripinfo-output", value=tripinfo_file)
        etree.SubElement(output_elem, "summary-output", value=summary_file)

        # Report 섹션
        report_elem = etree.SubElement(root, "report")
        etree.SubElement(report_elem, "verbose", value="true")
        etree.SubElement(report_elem, "no-warnings", value="true")
        etree.SubElement(report_elem, "no-step-log", value="true")

        tree = etree.ElementTree(root)
        tree.write(config_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")

        return config_path

    def run_simulation(
        self,
        config_file: str,
        output_dir: str,
        timeout: Optional[int] = 600
    ) -> Tuple[bool, Optional[str], Dict[str, str]]:
        """
        SUMO 시뮬레이션 실행

        Args:
            config_file: .sumocfg 파일
            output_dir: 출력 디렉토리
            timeout: 실행 제한 시간 (초)

        Returns:
            (성공 여부, 에러 메시지, 출력 파일 딕셔너리)
        """
        cmd = [
            self.sumo_binary,
            "-c", config_file,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"SUMO 실행 실패: {error_msg}")
                return False, error_msg, {}

            # 출력 파일 확인
            config_name = Path(config_file).stem
            tripinfo_file = os.path.join(output_dir, f"{config_name}.tripinfo.xml")
            summary_file = os.path.join(output_dir, f"{config_name}.summary.xml")

            output_files = {}
            if os.path.exists(tripinfo_file):
                output_files["tripinfo"] = tripinfo_file
            if os.path.exists(summary_file):
                output_files["summary"] = summary_file

            if not output_files:
                return False, "출력 파일이 생성되지 않았습니다", {}

            return True, None, output_files

        except subprocess.TimeoutExpired:
            return False, f"시뮬레이션 실행 시간 초과 ({timeout}초)", {}
        except FileNotFoundError:
            return False, f"SUMO 실행 파일을 찾을 수 없습니다: {self.sumo_binary}", {}
        except Exception as e:
            return False, str(e), {}

    def parse_tripinfo(self, tripinfo_file: str) -> Dict[str, Any]:
        """
        tripinfo.xml 파싱하여 통계 추출

        Args:
            tripinfo_file: tripinfo.xml 파일 경로

        Returns:
            통계 정보
        """
        try:
            tree = etree.parse(tripinfo_file)
            root = tree.getroot()

            tripinfos = root.findall(".//tripinfo")

            if not tripinfos:
                return {
                    "completed_trips": 0,
                    "avg_duration": 0.0,
                    "avg_waiting_time": 0.0,
                    "avg_time_loss": 0.0,
                }

            durations = []
            waiting_times = []
            time_losses = []

            for tripinfo in tripinfos:
                duration = float(tripinfo.get("duration", 0))
                waiting_time = float(tripinfo.get("waitingTime", 0))
                time_loss = float(tripinfo.get("timeLoss", 0))

                durations.append(duration)
                waiting_times.append(waiting_time)
                time_losses.append(time_loss)

            return {
                "completed_trips": len(tripinfos),
                "avg_duration": sum(durations) / len(durations) if durations else 0.0,
                "avg_waiting_time": sum(waiting_times) / len(waiting_times) if waiting_times else 0.0,
                "avg_time_loss": sum(time_losses) / len(time_losses) if time_losses else 0.0,
            }

        except Exception as e:
            print(f"tripinfo 파싱 실패: {e}")
            return {
                "completed_trips": 0,
                "avg_duration": 0.0,
                "avg_waiting_time": 0.0,
                "avg_time_loss": 0.0,
            }

    def parse_summary(self, summary_file: str) -> Dict[str, Any]:
        """
        summary.xml 파싱하여 시간별 통계 추출

        Args:
            summary_file: summary.xml 파일 경로

        Returns:
            통계 정보
        """
        try:
            tree = etree.parse(summary_file)
            root = tree.getroot()

            steps = root.findall(".//step")

            if not steps:
                return {
                    "total_steps": 0,
                    "avg_vehicles_running": 0.0,
                    "avg_mean_speed": 0.0,
                }

            vehicles_running = []
            mean_speeds = []

            for step in steps:
                running = int(step.get("running", 0))
                speed = float(step.get("meanSpeed", 0))

                vehicles_running.append(running)
                mean_speeds.append(speed)

            return {
                "total_steps": len(steps),
                "avg_vehicles_running": sum(vehicles_running) / len(vehicles_running) if vehicles_running else 0.0,
                "avg_mean_speed": sum(mean_speeds) / len(mean_speeds) if mean_speeds else 0.0,
            }

        except Exception as e:
            print(f"summary 파싱 실패: {e}")
            return {
                "total_steps": 0,
                "avg_vehicles_running": 0.0,
                "avg_mean_speed": 0.0,
            }

    def run_full_simulation(
        self,
        net_file: str,
        route_file: str,
        output_dir: str,
        simulation_id: str,
        duration_seconds: float = 3600.0,
        step_length: float = 1.0
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        전체 시뮬레이션 실행 프로세스

        Args:
            net_file: 네트워크 파일
            route_file: 경로 파일
            output_dir: 출력 디렉토리
            simulation_id: 시뮬레이션 ID
            duration_seconds: 시뮬레이션 시간 (초)
            step_length: 스텝 길이 (초)

        Returns:
            (성공 여부, 에러 메시지, 결과 통계)
        """
        os.makedirs(output_dir, exist_ok=True)

        # 1. sumocfg 생성
        config_file = self.create_sumocfg(
            net_file=net_file,
            route_file=route_file,
            output_dir=output_dir,
            config_name=simulation_id,
            begin=0.0,
            end=duration_seconds,
            step_length=step_length
        )

        # 2. SUMO 실행
        success, error, output_files = self.run_simulation(
            config_file=config_file,
            output_dir=output_dir
        )

        if not success:
            return False, error, {}

        # 3. 결과 파싱
        results = {
            "output_files": output_files,
            "tripinfo_stats": {},
            "summary_stats": {},
        }

        if "tripinfo" in output_files:
            results["tripinfo_stats"] = self.parse_tripinfo(output_files["tripinfo"])

        if "summary" in output_files:
            results["summary_stats"] = self.parse_summary(output_files["summary"])

        return True, None, results


def create_placeholder_simulation_results(
    output_dir: str,
    simulation_id: str,
    vehicle_count: int = 1000
) -> Dict[str, Any]:
    """
    SUMO가 없는 환경에서 placeholder 시뮬레이션 결과 생성
    """
    os.makedirs(output_dir, exist_ok=True)

    # Placeholder tripinfo.xml
    tripinfo_file = os.path.join(output_dir, f"{simulation_id}.tripinfo.xml")
    tripinfo_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<tripinfos xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/tripinfo_file.xsd">
    <!-- Placeholder simulation results for {simulation_id} -->
    <tripinfo id="veh_0" depart="0.00" departLane="edge1_0" departPos="5.00" departSpeed="0.00"
              departDelay="0.00" arrival="120.50" arrivalLane="edge2_0" arrivalPos="495.00"
              arrivalSpeed="13.89" duration="120.50" routeLength="1000.00" waitingTime="15.30"
              waitingCount="2" stopTime="0.00" timeLoss="25.80" rerouteNo="0" devices=""
              vType="car" speedFactor="1.00" vaporized=""/>
    <tripinfo id="veh_1" depart="10.00" departLane="edge1_0" departPos="5.00" departSpeed="0.00"
              departDelay="0.00" arrival="135.20" arrivalLane="edge2_0" arrivalPos="495.00"
              arrivalSpeed="13.89" duration="125.20" routeLength="1000.00" waitingTime="20.10"
              waitingCount="3" stopTime="0.00" timeLoss="30.50" rerouteNo="0" devices=""
              vType="car" speedFactor="1.00" vaporized=""/>
</tripinfos>
"""
    with open(tripinfo_file, "w", encoding="utf-8") as f:
        f.write(tripinfo_xml)

    # Placeholder summary.xml
    summary_file = os.path.join(output_dir, f"{simulation_id}.summary.xml")
    summary_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<summary xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/summary_file.xsd">
    <step time="0.00" loaded="100" inserted="10" running="10" waiting="90" ended="0" meanWaitingTime="0.00" meanTravelTime="0.00" meanSpeed="10.50" meanSpeedRelative="0.75" duration="0"/>
    <step time="100.00" loaded="100" inserted="50" running="45" waiting="50" ended="5" meanWaitingTime="15.30" meanTravelTime="120.50" meanSpeed="12.30" meanSpeedRelative="0.88" duration="100"/>
    <step time="200.00" loaded="100" inserted="80" running="70" waiting="20" ended="10" meanWaitingTime="18.20" meanTravelTime="125.20" meanSpeed="11.80" meanSpeedRelative="0.85" duration="200"/>
</summary>
"""
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_xml)

    return {
        "output_files": {
            "tripinfo": tripinfo_file,
            "summary": summary_file,
        },
        "tripinfo_stats": {
            "completed_trips": 2,
            "avg_duration": 122.85,
            "avg_waiting_time": 17.70,
            "avg_time_loss": 28.15,
        },
        "summary_stats": {
            "total_steps": 3,
            "avg_vehicles_running": 41.67,
            "avg_mean_speed": 11.53,
        },
    }
