"""
OD Matrix Demand Provider (Placeholder)

OD Matrix 기반 교통 수요 생성
"""

from typing import Any
from .demand_provider import DemandProvider, DemandData


class ODMatrixDemandProvider(DemandProvider):
    """
    OD Matrix 수요 생성기 (Placeholder)

    향후 구현:
    - OD Matrix 입력
    - Zone 기반 통행 생성
    - 실제 통행 패턴 반영
    """

    def generate_demand(
        self,
        network_data: Any,
        demand_config: dict,
    ) -> DemandData:
        """
        OD Matrix 기반 수요 생성 (현재 미구현)

        Args:
            network_data: NetworkData
            demand_config: {
                "od_matrix": OD Matrix (zone x zone),
                "zone_edges": Zone별 edge 매핑,
                "time_distribution": 시간대별 분포,
            }

        Returns:
            DemandData

        Raises:
            NotImplementedError: 아직 구현되지 않음
        """
        raise NotImplementedError(
            "ODMatrixDemandProvider는 아직 구현되지 않았습니다. "
            "ToyDemandProvider를 사용하거나 향후 OD Matrix 통합을 기다려주세요.\n\n"
            "구현 예정:\n"
            "1. OD Matrix 파싱 (CSV, JSON)\n"
            "2. Zone별 edge 매핑\n"
            "3. Zone 간 통행 생성\n"
            "4. 시간대별 분포 적용"
        )

    def apply_demand_multiplier(
        self,
        demand_data: DemandData,
        multiplier: float,
    ) -> DemandData:
        """
        수요 배율 적용 (현재 미구현)

        Args:
            demand_data: 원본 수요 데이터
            multiplier: 배율

        Returns:
            조정된 DemandData

        Raises:
            NotImplementedError: 아직 구현되지 않음
        """
        raise NotImplementedError(
            "ODMatrixDemandProvider.apply_demand_multiplier는 아직 구현되지 않았습니다."
        )
