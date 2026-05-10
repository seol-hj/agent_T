"""
Scenario Generator Service

ExperimentSpec으로부터 ScenarioPlan 및 빌드 요청 생성
"""

import time
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from common.schemas import (
    ExperimentSpec,
    ScenarioPlan,
    ScenarioVariant,
    ScenarioType,
    NetworkBuildRequest,
    DemandBuildRequest,
)

from ..models.scenario_output import ScenarioBuilderOutput, ScenarioModification


class ScenarioGenerator:
    """
    시나리오 생성기

    ExperimentSpec을 기반으로 Base/Alternative 시나리오 생성
    """

    def __init__(self):
        """초기화"""
        pass

    def generate_scenarios(
        self,
        experiment_spec: dict,
        request_type: str,
    ) -> ScenarioBuilderOutput:
        """
        ExperimentSpec으로부터 시나리오 생성

        Args:
            experiment_spec: ExperimentSpec JSON
            request_type: 요청 타입 (demand_increase, lane_change, signal_timing_change)

        Returns:
            ScenarioBuilderOutput (ScenarioPlan + NetworkBuildRequest + DemandBuildRequest)
        """
        start_time = time.time()

        # ExperimentSpec 파싱
        experiment_id = experiment_spec["experiment_id"]

        # 1. Baseline 시나리오 생성
        baseline_variant = self._create_baseline_variant(experiment_spec)

        # 2. Alternative 시나리오 생성 (요청 타입별)
        alternative_variants = self._create_alternative_variants(
            experiment_spec, request_type
        )

        # 3. ScenarioPlan 생성
        scenario_plan = self._create_scenario_plan(
            experiment_id=experiment_id,
            baseline=baseline_variant,
            alternatives=alternative_variants,
            objectives=experiment_spec.get("objectives", []),
        )

        # 4. NetworkBuildRequest 생성 (각 변형당 1개)
        network_requests = self._create_network_requests(
            experiment_spec=experiment_spec,
            baseline=baseline_variant,
            alternatives=alternative_variants,
        )

        # 5. DemandBuildRequest 생성 (각 변형당 1개)
        demand_requests = self._create_demand_requests(
            experiment_spec=experiment_spec,
            baseline=baseline_variant,
            alternatives=alternative_variants,
            request_type=request_type,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        return ScenarioBuilderOutput(
            scenario_plan=scenario_plan,
            network_requests=network_requests,
            demand_requests=demand_requests,
            experiment_id=experiment_id,
            baseline_variant_id=baseline_variant["variant_id"],
            alternative_variant_ids=[v["variant_id"] for v in alternative_variants],
            processing_time_ms=processing_time_ms,
        )

    def _create_baseline_variant(self, experiment_spec: dict) -> dict:
        """
        Baseline 시나리오 변형 생성

        현재 상태를 나타내는 Base 시나리오
        """
        experiment_id = experiment_spec["experiment_id"]
        variant_id = f"base-{experiment_id.split('-')[-1]}"

        return {
            "variant_id": variant_id,
            "variant_type": "baseline",
            "name": "현재 상태 (Baseline)",
            "description": "변경 사항 없이 현재 도로망 및 교통 수요 상태",
            "parameters": {
                "modifications": [],
                "demand_multiplier": 1.0,
                "network_changes": None,
            },
        }

    def _create_alternative_variants(
        self, experiment_spec: dict, request_type: str
    ) -> list[dict]:
        """
        Alternative 시나리오 변형 생성

        요청 타입에 따라 다른 Alternative 생성
        """
        experiment_id = experiment_spec["experiment_id"]
        alternatives = []

        if request_type == "demand_increase":
            # 교통량 증가 시나리오
            alternatives.append(
                self._create_demand_increase_variant(experiment_spec, suffix="001")
            )

        elif request_type == "lane_change":
            # 차로 변경 시나리오
            alternatives.append(
                self._create_lane_change_variant(experiment_spec, suffix="001")
            )

        elif request_type == "signal_timing_change":
            # 신호 타이밍 변경 시나리오
            alternatives.append(
                self._create_signal_timing_variant(experiment_spec, suffix="001")
            )

        return alternatives

    def _create_demand_increase_variant(
        self, experiment_spec: dict, suffix: str
    ) -> dict:
        """교통량 증가 시나리오"""
        experiment_id = experiment_spec["experiment_id"]
        variant_id = f"alt-demand-{suffix}"

        # 기본 20% 증가 (objectives에서 추출 가능)
        demand_multiplier = 1.2

        return {
            "variant_id": variant_id,
            "variant_type": "alternative",
            "name": "교통량 20% 증가",
            "description": "차량 수가 20% 증가했을 때의 교통 상황",
            "parameters": {
                "modifications": [],
                "demand_multiplier": demand_multiplier,
                "network_changes": None,
            },
        }

    def _create_lane_change_variant(
        self, experiment_spec: dict, suffix: str
    ) -> dict:
        """차로 변경 시나리오"""
        experiment_id = experiment_spec["experiment_id"]
        variant_id = f"alt-lane-{suffix}"

        return {
            "variant_id": variant_id,
            "variant_type": "alternative",
            "name": "주요 도로 차로 추가 (+1)",
            "description": "주요 병목 구간의 차로를 1개 추가",
            "parameters": {
                "modifications": [
                    {
                        "type": "lane_change",
                        "target": "major_edges",
                        "lane_delta": 1,
                        "description": "주요 도로의 차로 수 +1",
                    }
                ],
                "demand_multiplier": 1.0,
                "network_changes": {
                    "lane_modifications": {
                        "strategy": "increase_major_roads",
                        "lane_delta": 1,
                    }
                },
            },
        }

    def _create_signal_timing_variant(
        self, experiment_spec: dict, suffix: str
    ) -> dict:
        """신호 타이밍 변경 시나리오"""
        experiment_id = experiment_spec["experiment_id"]
        variant_id = f"alt-signal-{suffix}"

        return {
            "variant_id": variant_id,
            "variant_type": "alternative",
            "name": "신호 체계 최적화",
            "description": "AI 기반으로 최적화된 신호등 타이밍",
            "parameters": {
                "modifications": [
                    {
                        "type": "traffic_light",
                        "target": "all_junctions",
                        "cycle": 90,
                        "green_split": 0.55,
                        "description": "신호 주기 90초, 녹색 시간 55%",
                    }
                ],
                "demand_multiplier": 1.0,
                "network_changes": {
                    "signal_timing": {
                        "strategy": "optimize_cycle",
                        "cycle_seconds": 90,
                        "green_time_ratio": 0.55,
                    }
                },
            },
        }

    def _create_scenario_plan(
        self,
        experiment_id: str,
        baseline: dict,
        alternatives: list[dict],
        objectives: list[str],
    ) -> dict:
        """ScenarioPlan 생성"""
        plan_id = f"plan-{experiment_id.split('-')[-1]}"

        return {
            "schema_version": "1.0",
            "plan_id": plan_id,
            "experiment_id": experiment_id,
            "baseline": baseline,
            "alternatives": alternatives,
            "comparison_objectives": objectives,
            "created_at": datetime.utcnow().isoformat(),
        }

    def _create_network_requests(
        self,
        experiment_spec: dict,
        baseline: dict,
        alternatives: list[dict],
    ) -> list[dict]:
        """
        NetworkBuildRequest 생성

        각 변형당 1개씩 생성 (Baseline + Alternatives)
        """
        experiment_id = experiment_spec["experiment_id"]
        location = experiment_spec.get("location", {})
        requests = []

        # Baseline 도로망 요청
        requests.append(
            self._create_network_request(
                experiment_id=experiment_id,
                variant_id=baseline["variant_id"],
                location=location,
                modifications=None,
            )
        )

        # Alternative 도로망 요청
        for alt in alternatives:
            modifications = alt["parameters"].get("network_changes")
            requests.append(
                self._create_network_request(
                    experiment_id=experiment_id,
                    variant_id=alt["variant_id"],
                    location=location,
                    modifications=modifications,
                )
            )

        return requests

    def _create_network_request(
        self,
        experiment_id: str,
        variant_id: str,
        location: dict,
        modifications: Optional[dict],
    ) -> dict:
        """개별 NetworkBuildRequest 생성"""
        request_id = f"netreq-{experiment_id.split('-')[-1]}-{variant_id}"

        osm_source = {
            "type": "bbox",
            "bbox": location.get("bbox"),
            "query": location.get("osm_query") or location.get("region"),
        }

        network_options = {
            "vehicle_types": ["passenger", "bus", "truck"],
            "tls_guess": True,
            "speed_limits": True,
            "geometry_remove": True,
        }

        # modifications를 SUMO 형식으로 변환
        mod_list = None
        if modifications:
            mod_list = self._convert_network_modifications(modifications)

        return {
            "schema_version": "1.0",
            "request_id": request_id,
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "osm_source": osm_source,
            "network_options": network_options,
            "modifications": mod_list,
            "created_at": datetime.utcnow().isoformat(),
        }

    def _convert_network_modifications(self, network_changes: dict) -> list[dict]:
        """
        네트워크 변경사항을 SUMO modifications 형식으로 변환

        예: lane_modifications → edge 수정 목록
            signal_timing → traffic_light 수정 목록
        """
        modifications = []

        # 차로 변경
        if "lane_modifications" in network_changes:
            lane_mod = network_changes["lane_modifications"]
            modifications.append(
                {
                    "type": "lane_change",
                    "strategy": lane_mod.get("strategy", "increase_major_roads"),
                    "lane_delta": lane_mod.get("lane_delta", 1),
                    "target_edges": "major",  # 실제로는 Network Builder가 결정
                }
            )

        # 신호 타이밍 변경
        if "signal_timing" in network_changes:
            signal_mod = network_changes["signal_timing"]
            modifications.append(
                {
                    "type": "traffic_light",
                    "strategy": signal_mod.get("strategy", "optimize_cycle"),
                    "cycle_seconds": signal_mod.get("cycle_seconds", 90),
                    "green_time_ratio": signal_mod.get("green_time_ratio", 0.55),
                    "target_junctions": "all",  # 실제로는 Network Builder가 결정
                }
            )

        return modifications if modifications else None

    def _create_demand_requests(
        self,
        experiment_spec: dict,
        baseline: dict,
        alternatives: list[dict],
        request_type: str,
    ) -> list[dict]:
        """
        DemandBuildRequest 생성

        각 변형당 1개씩 생성 (Baseline + Alternatives)
        """
        experiment_id = experiment_spec["experiment_id"]
        traffic_settings = experiment_spec.get("traffic_settings", {})
        time_settings = experiment_spec.get("time_settings", {})
        requests = []

        # Baseline 수요 요청
        requests.append(
            self._create_demand_request(
                experiment_id=experiment_id,
                variant_id=baseline["variant_id"],
                traffic_settings=traffic_settings,
                time_settings=time_settings,
                demand_multiplier=1.0,
            )
        )

        # Alternative 수요 요청
        for alt in alternatives:
            demand_multiplier = alt["parameters"].get("demand_multiplier", 1.0)
            requests.append(
                self._create_demand_request(
                    experiment_id=experiment_id,
                    variant_id=alt["variant_id"],
                    traffic_settings=traffic_settings,
                    time_settings=time_settings,
                    demand_multiplier=demand_multiplier,
                )
            )

        return requests

    def _create_demand_request(
        self,
        experiment_id: str,
        variant_id: str,
        traffic_settings: dict,
        time_settings: dict,
        demand_multiplier: float,
    ) -> dict:
        """개별 DemandBuildRequest 생성"""
        request_id = f"demreq-{experiment_id.split('-')[-1]}-{variant_id}"
        network_artifact_id = f"net-{experiment_id.split('-')[-1]}-{variant_id}"

        base_vehicle_count = traffic_settings.get("vehicle_count", 5000)
        adjusted_vehicle_count = int(base_vehicle_count * demand_multiplier)

        vehicle_distribution = traffic_settings.get(
            "vehicle_distribution", {"passenger": 0.8, "bus": 0.1, "truck": 0.1}
        )

        # 시간 설정 (초 단위)
        start_time = self._time_to_seconds(time_settings.get("start_time", "07:00"))
        end_time = self._time_to_seconds(time_settings.get("end_time", "09:00"))

        demand_settings = {
            "vehicle_count": adjusted_vehicle_count,
            "start_time": start_time,
            "end_time": end_time,
            "vehicle_types": vehicle_distribution,
            "trip_distribution": "random",
            "departure_distribution": "uniform",
        }

        return {
            "schema_version": "1.0",
            "request_id": request_id,
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "network_artifact_id": network_artifact_id,
            "demand_settings": demand_settings,
            "created_at": datetime.utcnow().isoformat(),
        }

    def _time_to_seconds(self, time_str: str) -> int:
        """시간 문자열 (HH:MM) → 초 변환"""
        if isinstance(time_str, int):
            return time_str

        try:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 3600 + minutes * 60
        except:
            return 0
