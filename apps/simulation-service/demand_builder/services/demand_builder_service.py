"""
Demand Builder Service

DemandBuildRequest → DemandArtifact 변환
"""

import time
import io
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas import DemandBuildRequest, DemandArtifact
from common.gateways.storage import StorageGateway

from ..providers.demand_provider import DemandProvider
from ..providers.toy_demand_provider import ToyDemandProvider
from ..providers.od_matrix_demand_provider import ODMatrixDemandProvider
from .route_generator import RouteGenerator


class DemandBuilderService:
    """
    Demand Builder 서비스

    DemandBuildRequest를 받아 DemandArtifact 생성
    """

    def __init__(self, storage_gateway: StorageGateway):
        """
        Args:
            storage_gateway: 스토리지 Gateway
        """
        self.storage = storage_gateway
        self.route_generator = RouteGenerator()

        # Provider 초기화
        self.providers = {
            "toy": ToyDemandProvider(random_seed=42),
            "od_matrix": ODMatrixDemandProvider(),  # Placeholder
        }

    async def build_demand(
        self,
        request: dict,
        network_artifact: Optional[dict] = None,
    ) -> dict:
        """
        교통 수요 빌드

        Args:
            request: DemandBuildRequest JSON
            network_artifact: NetworkArtifact JSON (선택적, 실제 도로망 필요 시)

        Returns:
            DemandArtifact JSON
        """
        start_time = time.time()

        # 1. DemandBuildRequest 파싱
        experiment_id = request["experiment_id"]
        variant_id = request["variant_id"]
        request_id = request["request_id"]
        demand_settings = request["demand_settings"]

        # 2. Provider 선택
        provider_type = demand_settings.get("provider_type", "toy")
        if provider_type not in self.providers:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        provider = self.providers[provider_type]

        # 3. 네트워크 데이터 준비 (Toy는 간단한 구조 사용)
        # 실제로는 network_artifact에서 로드해야 하지만, 초기 구현에서는 Mock
        network_data = self._create_mock_network_data()

        # 4. 교통 수요 생성
        try:
            demand_data = provider.generate_demand(
                network_data=network_data,
                demand_config=demand_settings,
            )
        except NotImplementedError as e:
            # OD Matrix Provider가 아직 미구현인 경우 Toy로 폴백
            print(f"Warning: {e}")
            print("Falling back to ToyDemandProvider...")
            provider = self.providers["toy"]
            demand_data = provider.generate_demand(
                network_data=network_data,
                demand_config=demand_settings,
            )

        # 5. demand_multiplier 적용 (이미 demand_settings에 반영되어 있으면 생략 가능)
        # 여기서는 명시적으로 확인
        multiplier = demand_settings.get("demand_multiplier", 1.0)
        if multiplier != 1.0:
            # 이미 vehicle_count에 반영되어 있으므로 추가 적용 불필요
            # 하지만 명시적으로 적용하려면:
            # demand_data = provider.apply_demand_multiplier(demand_data, multiplier)
            pass

        # 6. SUMO .rou.xml 생성
        xml_content = self.route_generator.generate_xml(demand_data)
        xml_bytes = xml_content.encode('utf-8')

        # 7. 스토리지에 저장
        file_path = f"{experiment_id}/{variant_id}/routes.rou.xml"
        uri = await self.storage.upload(
            file_path=file_path,
            content=xml_bytes,
        )

        # 8. 통계 계산
        statistics = self.route_generator.calculate_statistics(demand_data)

        # 9. DemandArtifact 생성
        artifact_id = f"dem-{experiment_id.split('-')[-1]}-{variant_id}"

        artifact = {
            "schema_version": "1.0",
            "artifact_id": artifact_id,
            "request_id": request_id,
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "uri": uri,
            "file_format": "rou.xml",
            "file_size_bytes": len(xml_bytes),
            "statistics": statistics,
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "demand-builder-v0.1.0",
        }

        processing_time_ms = (time.time() - start_time) * 1000
        print(f"Demand built in {processing_time_ms:.1f}ms: {uri}")

        return artifact

    def _create_mock_network_data(self):
        """
        Mock 네트워크 데이터 생성

        실제로는 NetworkArtifact에서 .net.xml을 파싱하거나
        NetworkData 객체를 전달받아야 함
        """
        class MockNetworkData:
            def __init__(self):
                # 간단한 그리드 엣지
                self.edges = [
                    {"id": "e_0", "from": "n_0_0", "to": "n_0_1"},
                    {"id": "e_1", "from": "n_0_1", "to": "n_0_0"},
                    {"id": "e_2", "from": "n_0_1", "to": "n_1_1"},
                    {"id": "e_3", "from": "n_1_1", "to": "n_0_1"},
                    {"id": "e_4", "from": "n_1_0", "to": "n_1_1"},
                    {"id": "e_5", "from": "n_1_1", "to": "n_1_0"},
                    {"id": "e_6", "from": "n_0_0", "to": "n_1_0"},
                    {"id": "e_7", "from": "n_1_0", "to": "n_0_0"},
                ]

        return MockNetworkData()
