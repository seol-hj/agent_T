"""
Analysis Service

시뮬레이션 결과 분석 전체 흐름 관리
"""

import time
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas import AnalysisRequest, AnalysisResult
from common.gateways.storage import StorageGateway

from ..parsers.sumo_result_parser import SumoResultParser
from .kpi_engine import KPIEngine
from .scenario_comparator import ScenarioComparator


class AnalysisService:
    """
    분석 서비스

    AnalysisRequest → KPI 추출 → 시나리오 비교 → AnalysisResult
    """

    def __init__(self, storage_gateway: StorageGateway):
        """
        Args:
            storage_gateway: 스토리지 Gateway
        """
        self.storage = storage_gateway
        self.parser = SumoResultParser()
        self.kpi_engine = KPIEngine()
        self.comparator = ScenarioComparator()

    async def analyze(self, request: dict) -> dict:
        """
        시뮬레이션 결과 분석

        Args:
            request: AnalysisRequest JSON

        Returns:
            AnalysisResult JSON
        """
        start_time = time.time()

        # 1. Request 파싱
        experiment_id = request["experiment_id"]
        request_id = request["request_id"]
        baseline_simulation = request["baseline_simulation"]
        alternative_simulations = request["alternative_simulations"]

        # 2. Baseline KPI 추출
        baseline_kpis = await self._extract_kpis(baseline_simulation)

        # 3. Alternative KPI 추출 (여러 개 가능)
        alternative_kpis_list = []
        for alt_sim in alternative_simulations:
            alt_kpis = await self._extract_kpis(alt_sim)
            alternative_kpis_list.append({
                "variant_id": alt_sim["variant_id"],
                "kpis": alt_kpis,
            })

        # 4. 시나리오 비교 (첫 번째 alternative만 비교, 향후 확장 가능)
        if alternative_kpis_list:
            first_alt = alternative_kpis_list[0]
            comparison = self.comparator.compare_scenarios(
                baseline_kpis=baseline_kpis,
                alternative_kpis=first_alt["kpis"],
            )
            improvements = comparison["improvements"]
            overall_score = self.comparator.calculate_overall_score(improvements)
            summary = self.comparator.generate_summary(comparison)
        else:
            improvements = {}
            overall_score = 0.0
            summary = "Alternative 시나리오가 없습니다."

        # 5. AnalysisResult 생성
        processing_time_ms = (time.time() - start_time) * 1000

        result = {
            "schema_version": "1.0",
            "analysis_id": f"ana-{experiment_id.split('-')[-1]}",
            "request_id": request_id,
            "experiment_id": experiment_id,
            "kpi_comparison": {
                "baseline_kpis": baseline_kpis,
                "alternative_kpis": first_alt["kpis"] if alternative_kpis_list else {},
                "improvements": improvements,
            },
            "overall_score": overall_score,
            "summary": summary,
            "created_at": datetime.utcnow().isoformat(),
            "processing_time_ms": processing_time_ms,
            "analyzed_by": "analyzer-v0.1.0",
        }

        print(f"Analysis completed in {processing_time_ms:.1f}ms")

        return result

    async def _extract_kpis(self, simulation_artifact: dict) -> dict:
        """
        시뮬레이션 아티팩트에서 KPI 추출

        Args:
            simulation_artifact: SimulationRunArtifact JSON

        Returns:
            KPI dict
        """
        outputs = simulation_artifact.get("outputs", {})

        # 1. 출력 파일 다운로드
        tripinfo_xml = await self._download_output(outputs.get("tripinfo"))
        summary_xml = await self._download_output(outputs.get("summary"))
        queue_xml = await self._download_output(outputs.get("queue"))
        emission_xml = await self._download_output(outputs.get("emission"))

        # 2. XML 파싱
        trips = self.parser.parse_tripinfo(tripinfo_xml) if tripinfo_xml else []
        summary_steps = self.parser.parse_summary(summary_xml) if summary_xml else []
        queues = self.parser.parse_queue(queue_xml) if queue_xml else []
        emissions = self.parser.parse_emission(emission_xml) if emission_xml else []

        # 3. KPI 계산
        kpis = self.kpi_engine.calculate_kpis(
            trips=trips,
            summary_steps=summary_steps,
            queues=queues,
            emissions=emissions,
        )

        return kpis

    async def _download_output(self, uri: Optional[str]) -> Optional[str]:
        """
        출력 파일 다운로드

        Args:
            uri: 파일 URI

        Returns:
            파일 내용 (문자열) 또는 None
        """
        if not uri:
            return None

        try:
            content_bytes = await self.storage.download(uri)
            return content_bytes.decode('utf-8')
        except Exception as e:
            print(f"Warning: Failed to download {uri}: {e}")
            return None
