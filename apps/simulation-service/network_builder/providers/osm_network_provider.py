"""
OSM Network Provider (Placeholder)

OpenStreetMap 데이터로부터 실제 도로망 생성
"""

from typing import Optional
from .network_provider import NetworkProvider, NetworkData


class OSMNetworkProvider(NetworkProvider):
    """
    OSM 도로망 생성기 (Placeholder)

    향후 구현:
    - Overpass API로 OSM 데이터 다운로드
    - netconvert 또는 osmium으로 변환
    - SUMO 도로망 생성
    """

    def generate_network(
        self,
        source_config: dict,
        network_options: Optional[dict] = None,
    ) -> NetworkData:
        """
        OSM 도로망 생성 (현재 미구현)

        Args:
            source_config: {"type": "bbox", "bbox": [lon_min, lat_min, lon_max, lat_max]}
            network_options: 네트워크 옵션

        Returns:
            NetworkData

        Raises:
            NotImplementedError: 아직 구현되지 않음
        """
        raise NotImplementedError(
            "OSMNetworkProvider는 아직 구현되지 않았습니다. "
            "ToyNetworkProvider를 사용하거나 향후 OSM 통합을 기다려주세요.\n\n"
            "구현 예정:\n"
            "1. Overpass API로 bbox 범위의 OSM 데이터 다운로드\n"
            "2. osmium 또는 netconvert로 SUMO 네트워크 변환\n"
            "3. NetworkData 구조로 파싱"
        )

    def apply_modifications(
        self,
        network_data: NetworkData,
        modifications: list[dict],
    ) -> NetworkData:
        """
        도로망 수정사항 적용 (현재 미구현)

        Args:
            network_data: 원본 도로망 데이터
            modifications: 수정사항 목록

        Returns:
            수정된 NetworkData

        Raises:
            NotImplementedError: 아직 구현되지 않음
        """
        raise NotImplementedError(
            "OSMNetworkProvider.apply_modifications는 아직 구현되지 않았습니다."
        )
