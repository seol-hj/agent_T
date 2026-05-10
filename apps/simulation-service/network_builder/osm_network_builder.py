"""
OSM Network Builder

OpenStreetMap 데이터를 다운로드하고 SUMO 도로망으로 변환
"""
import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import httpx
from lxml import etree


class OSMNetworkBuilder:
    """OSM 데이터를 SUMO 도로망으로 변환하는 빌더"""

    # Overpass API endpoint
    OVERPASS_API = "https://overpass-api.de/api/interpreter"

    def __init__(self, sumo_tools_path: Optional[str] = None):
        """
        Args:
            sumo_tools_path: SUMO tools 경로 (없으면 환경변수 SUMO_HOME 사용)
        """
        self.sumo_tools_path = sumo_tools_path or os.getenv("SUMO_HOME", "/usr/share/sumo")
        self.netconvert_path = self._find_netconvert()

    def _find_netconvert(self) -> str:
        """netconvert 실행 파일 찾기"""
        # 1. 시스템 PATH에서 찾기
        try:
            result = subprocess.run(
                ["which", "netconvert"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # 2. SUMO_HOME/bin에서 찾기
        netconvert_bin = os.path.join(self.sumo_tools_path, "bin", "netconvert")
        if os.path.exists(netconvert_bin):
            return netconvert_bin

        # 3. Docker 환경에서는 /usr/bin/netconvert 시도
        if os.path.exists("/usr/bin/netconvert"):
            return "/usr/bin/netconvert"

        # 4. Fallback: 그냥 명령어 이름만 (PATH에 있을 것으로 가정)
        return "netconvert"

    async def download_osm(
        self,
        bbox: Tuple[float, float, float, float],
        output_path: str
    ) -> bool:
        """
        Overpass API를 통해 OSM 데이터 다운로드

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            output_path: OSM 파일 저장 경로

        Returns:
            성공 여부
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        # Overpass QL query
        query = f"""
        [out:xml][timeout:60];
        (
          way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});
          node(w);
        );
        out body;
        >;
        out skel qt;
        """

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.OVERPASS_API,
                    data={"data": query}
                )
                response.raise_for_status()

                # OSM XML 저장
                with open(output_path, "wb") as f:
                    f.write(response.content)

                return True

        except Exception as e:
            print(f"OSM 다운로드 실패: {e}")
            return False

    def convert_osm_to_net(
        self,
        osm_file: str,
        net_file: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        netconvert를 사용하여 OSM → SUMO network 변환

        Args:
            osm_file: OSM XML 파일 경로
            net_file: 출력 .net.xml 파일 경로
            options: netconvert 추가 옵션

        Returns:
            (성공 여부, 에러 메시지)
        """
        default_options = {
            "osm-files": osm_file,
            "output-file": net_file,
            "geometry.remove": True,
            "roundabouts.guess": True,
            "junctions.join": True,
            "tls.guess-signals": True,
            "tls.discard-simple": True,
            "tls.join": True,
            "ramps.guess": True,
            "junctions.corner-detail": 5,
            "output.street-names": True,
            "output.original-names": True,
        }

        if options:
            default_options.update(options)

        # netconvert 명령어 구성
        cmd = [self.netconvert_path]
        for key, value in default_options.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"netconvert 실패: {error_msg}")
                return False, error_msg

            # 생성된 파일 검증
            if not os.path.exists(net_file):
                return False, "net.xml 파일이 생성되지 않았습니다"

            # 파일 크기 확인
            file_size = os.path.getsize(net_file)
            if file_size < 100:  # 너무 작으면 실패로 간주
                return False, "생성된 net.xml 파일이 너무 작습니다"

            return True, None

        except FileNotFoundError:
            return False, f"netconvert를 찾을 수 없습니다: {self.netconvert_path}"
        except Exception as e:
            return False, str(e)

    def parse_network_stats(self, net_file: str) -> Dict[str, int]:
        """
        생성된 네트워크 통계 추출

        Args:
            net_file: .net.xml 파일 경로

        Returns:
            통계 정보 (edge_count, junction_count, tlLogic_count)
        """
        try:
            tree = etree.parse(net_file)
            root = tree.getroot()

            edge_count = len(root.findall(".//edge"))
            junction_count = len(root.findall(".//junction"))
            tl_count = len(root.findall(".//tlLogic"))

            return {
                "edge_count": edge_count,
                "junction_count": junction_count,
                "traffic_light_count": tl_count,
            }
        except Exception as e:
            print(f"네트워크 통계 파싱 실패: {e}")
            return {
                "edge_count": 0,
                "junction_count": 0,
                "traffic_light_count": 0,
            }

    async def build_network(
        self,
        location: Dict[str, Any],
        output_dir: str,
        network_id: str
    ) -> Tuple[bool, Optional[str], Dict[str, int]]:
        """
        전체 네트워크 빌드 프로세스

        Args:
            location: 위치 정보 (bbox 또는 center + radius)
            output_dir: 출력 디렉토리
            network_id: 네트워크 ID

        Returns:
            (성공 여부, 네트워크 파일 경로, 통계)
        """
        os.makedirs(output_dir, exist_ok=True)

        # 1. bbox 추출
        if "bbox" in location:
            bbox = tuple(location["bbox"])
        elif "center" in location and "radius_km" in location:
            # center + radius → bbox 변환 (간단한 근사)
            lon, lat = location["center"]
            radius_km = location["radius_km"]
            # 1km ≈ 0.01 degree (위도/경도)
            delta = radius_km * 0.01
            bbox = (lon - delta, lat - delta, lon + delta, lat + delta)
        else:
            return False, None, {}

        # 2. OSM 다운로드
        osm_file = os.path.join(output_dir, f"{network_id}.osm.xml")
        success = await self.download_osm(bbox, osm_file)
        if not success:
            return False, None, {}

        # 3. OSM → SUMO network 변환
        net_file = os.path.join(output_dir, f"{network_id}.net.xml")
        success, error = self.convert_osm_to_net(osm_file, net_file)
        if not success:
            return False, None, {}

        # 4. 통계 추출
        stats = self.parse_network_stats(net_file)

        # 5. OSM 파일 삭제 (용량 절약)
        try:
            os.remove(osm_file)
        except Exception:
            pass

        return True, net_file, stats


# Fallback: netconvert가 없는 환경에서 placeholder 네트워크 생성
def create_placeholder_network(net_file: str, network_id: str) -> Dict[str, int]:
    """
    netconvert가 없는 환경에서 placeholder 네트워크 생성
    (개발/테스트용)
    """
    placeholder_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<net version="1.16" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">
    <location netOffset="0.00,0.00" convBoundary="0.00,0.00,1000.00,1000.00" origBoundary="0.00,0.00,1000.00,1000.00" projParameter="!"/>

    <!-- Placeholder network for {network_id} -->
    <edge id="edge1" from="J1" to="J2" priority="1">
        <lane id="edge1_0" index="0" speed="13.89" length="500.00" shape="0.00,0.00 500.00,0.00"/>
    </edge>
    <edge id="edge2" from="J2" to="J3" priority="1">
        <lane id="edge2_0" index="0" speed="13.89" length="500.00" shape="500.00,0.00 1000.00,0.00"/>
    </edge>
    <edge id="edge3" from="J1" to="J4" priority="1">
        <lane id="edge3_0" index="0" speed="13.89" length="500.00" shape="0.00,0.00 0.00,500.00"/>
    </edge>

    <junction id="J1" type="priority" x="0.00" y="0.00" incLanes="" intLanes="" shape="0.00,1.60 0.00,-1.60 -1.60,0.00 1.60,0.00">
        <request index="0" response="0" foes="0" cont="0"/>
    </junction>
    <junction id="J2" type="priority" x="500.00" y="0.00" incLanes="edge1_0" intLanes="" shape="500.00,1.60 500.00,-1.60 500.00,1.60">
        <request index="0" response="0" foes="0" cont="0"/>
    </junction>
    <junction id="J3" type="priority" x="1000.00" y="0.00" incLanes="edge2_0" intLanes="" shape="1000.00,0.00 1000.00,-1.60 1000.00,0.00">
        <request index="0" response="0" foes="0" cont="0"/>
    </junction>
    <junction id="J4" type="priority" x="0.00" y="500.00" incLanes="edge3_0" intLanes="" shape="0.00,500.00 -1.60,500.00 0.00,500.00">
        <request index="0" response="0" foes="0" cont="0"/>
    </junction>
</net>
"""

    with open(net_file, "w", encoding="utf-8") as f:
        f.write(placeholder_xml)

    return {
        "edge_count": 3,
        "junction_count": 4,
        "traffic_light_count": 0,
    }
