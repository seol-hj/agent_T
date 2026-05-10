"""
Network Builder Service

NetworkBuildRequest → NetworkArtifact 변환
"""

import time
import io
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas import NetworkBuildRequest, NetworkArtifact
from common.gateways.storage import StorageGateway

from ..providers.network_provider import NetworkProvider
from ..providers.toy_network_provider import ToyNetworkProvider
from ..providers.osm_network_provider import OSMNetworkProvider
from .sumo_network_generator import SumoNetworkGenerator


class NetworkBuilderService:
    """
    Network Builder 서비스

    NetworkBuildRequest를 받아 NetworkArtifact 생성
    """

    def __init__(self, storage_gateway: StorageGateway):
        """
        Args:
            storage_gateway: 스토리지 Gateway
        """
        self.storage = storage_gateway
        self.sumo_generator = SumoNetworkGenerator()

        # Provider 초기화
        self.providers = {
            "toy": ToyNetworkProvider(),
            "osm": OSMNetworkProvider(),  # Placeholder
            "bbox": OSMNetworkProvider(),  # OSM bbox
        }

    async def build_network(
        self,
        request: dict,
    ) -> dict:
        """
        도로망 빌드

        Args:
            request: NetworkBuildRequest JSON

        Returns:
            NetworkArtifact JSON
        """
        start_time = time.time()

        # 1. NetworkBuildRequest 파싱
        experiment_id = request["experiment_id"]
        variant_id = request["variant_id"]
        request_id = request["request_id"]
        osm_source = request["osm_source"]
        network_options = request.get("network_options", {})
        modifications = request.get("modifications")

        # 2. Provider 선택
        source_type = osm_source.get("type", "toy")
        if source_type not in self.providers:
            raise ValueError(f"Unsupported source type: {source_type}")

        provider = self.providers[source_type]

        # 3. 도로망 생성
        try:
            network_data = provider.generate_network(
                source_config=osm_source,
                network_options=network_options,
            )
        except NotImplementedError as e:
            # OSM Provider가 아직 미구현인 경우 Toy로 폴백
            print(f"Warning: {e}")
            print("Falling back to ToyNetworkProvider...")
            provider = self.providers["toy"]
            network_data = provider.generate_network(
                source_config={"type": "toy", "grid_size": [3, 3]},
                network_options=network_options,
            )

        # 4. 수정사항 적용
        if modifications:
            network_data = provider.apply_modifications(
                network_data=network_data,
                modifications=modifications,
            )

        # 5. SUMO .net.xml 생성
        xml_content = self.sumo_generator.generate_xml(network_data)
        xml_bytes = xml_content.encode('utf-8')

        # 6. 스토리지에 저장
        file_path = f"{experiment_id}/{variant_id}/network.net.xml"
        uri = await self.storage.upload(
            file_path=file_path,
            content=xml_bytes,
        )

        # 7. 통계 계산
        statistics = self.sumo_generator.calculate_statistics(network_data)

        # 8. NetworkArtifact 생성
        artifact_id = f"net-{experiment_id.split('-')[-1]}-{variant_id}"

        artifact = {
            "schema_version": "1.0",
            "artifact_id": artifact_id,
            "request_id": request_id,
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "uri": uri,
            "file_format": "net.xml",
            "file_size_bytes": len(xml_bytes),
            "statistics": statistics,
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "network-builder-v0.1.0",
        }

        processing_time_ms = (time.time() - start_time) * 1000
        print(f"Network built in {processing_time_ms:.1f}ms: {uri}")

        return artifact
