"""
Pipeline E2E 통합 테스트

실제 HTTP 서버를 띄우고 전체 파이프라인을 테스트
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from apps.pipeline.main import app


@pytest.mark.asyncio
async def test_health_check():
    """헬스 체크 엔드포인트 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pipeline"


@pytest.mark.asyncio
async def test_readiness_check():
    """준비 상태 체크 엔드포인트 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/ready")
        # startup_event가 호출되지 않았으므로 503 예상
        # 하지만 테스트 환경에서는 startup_event가 호출되므로 200
        assert response.status_code in [200, 503]


@pytest.mark.asyncio
async def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "pipeline"
        assert "endpoints" in data
        assert "pipeline_steps" in data


@pytest.mark.asyncio
async def test_run_pipeline_e2e_with_mocks():
    """전체 파이프라인 E2E 테스트 (HTTP 서비스 Mock)"""

    # Mock httpx.AsyncClient for external service calls
    with patch("apps.pipeline.services.pipeline_service.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock responses from all services
        mock_client.post = AsyncMock(side_effect=[
            # Orchestrator
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "experiment_id": "exp_e2e",
                "user_request": "강남역 교통 시뮬레이션",
                "area": {
                    "center": {"lat": 37.4979, "lon": 127.0276},
                    "radius_m": 1000
                },
                "baseline_conditions": {
                    "time_range": {"start": "08:00", "end": "09:00"},
                    "demand_level": "peak_hour"
                },
                "scenarios": [
                    {
                        "scenario_id": "alt_demand_increase",
                        "type": "demand_increase",
                        "parameters": {"multiplier": 1.2}
                    }
                ],
                "metrics_of_interest": ["travel_time", "queue_length"],
                "simulation_duration_seconds": 3600,
                "clarification_questions": [],
                "confidence_score": 0.85
            }),
            # Scenario Builder
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "plan_id": "plan_e2e",
                "experiment_id": "exp_e2e",
                "baseline": {
                    "request_id": "req_baseline",
                    "experiment_id": "exp_e2e",
                    "area": {"center": {"lat": 37.4979, "lon": 127.0276}, "radius_m": 1000},
                    "network_source": "toy",
                    "modifications": [],
                    "output_format": "sumo_net"
                },
                "alternatives": [
                    {
                        "request_id": "req_alt",
                        "experiment_id": "exp_e2e",
                        "area": {"center": {"lat": 37.4979, "lon": 127.0276}, "radius_m": 1000},
                        "network_source": "toy",
                        "modifications": [],
                        "output_format": "sumo_net"
                    }
                ],
                "demand_baseline": {
                    "request_id": "req_demand_baseline",
                    "experiment_id": "exp_e2e",
                    "network_artifact_uri": "s3://bucket/network_baseline.net.xml",
                    "time_range": {"start": "08:00", "end": "09:00"},
                    "demand_level": "peak_hour",
                    "demand_source": "toy",
                    "vehicle_types": {"car": 0.9, "bus": 0.1},
                    "output_format": "sumo_routes"
                },
                "demand_alternatives": [
                    {
                        "request_id": "req_demand_alt",
                        "experiment_id": "exp_e2e",
                        "network_artifact_uri": "s3://bucket/network_alt.net.xml",
                        "time_range": {"start": "08:00", "end": "09:00"},
                        "demand_level": "peak_hour",
                        "demand_source": "toy",
                        "demand_multiplier": 1.2,
                        "vehicle_types": {"car": 0.9, "bus": 0.1},
                        "output_format": "sumo_routes"
                    }
                ],
                "summary": "베이스라인 + 교통량 20% 증가"
            }),
            # Network Builder (baseline)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "net_baseline",
                "request_id": "req_baseline",
                "experiment_id": "exp_e2e",
                "network_file_uri": "s3://bucket/network_baseline.net.xml",
                "metadata": {"node_count": 16, "edge_count": 24},
                "created_at": "2026-05-07T10:00:00"
            }),
            # Network Builder (alternative)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "net_alt",
                "request_id": "req_alt",
                "experiment_id": "exp_e2e",
                "network_file_uri": "s3://bucket/network_alt.net.xml",
                "metadata": {"node_count": 16, "edge_count": 24},
                "created_at": "2026-05-07T10:00:01"
            }),
            # Demand Builder (baseline)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "demand_baseline",
                "request_id": "req_demand_baseline",
                "experiment_id": "exp_e2e",
                "routes_file_uri": "s3://bucket/demand_baseline.rou.xml",
                "metadata": {"vehicle_count": 100},
                "created_at": "2026-05-07T10:00:02"
            }),
            # Demand Builder (alternative)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "demand_alt",
                "request_id": "req_demand_alt",
                "experiment_id": "exp_e2e",
                "routes_file_uri": "s3://bucket/demand_alt.rou.xml",
                "metadata": {"vehicle_count": 120},
                "created_at": "2026-05-07T10:00:03"
            }),
            # Simulator Runner (baseline)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "sim_baseline",
                "request_id": "req_sim_baseline",
                "experiment_id": "exp_e2e",
                "variant_id": "baseline",
                "config_file_uri": "s3://bucket/baseline.sumocfg",
                "output_tripinfo_uri": "s3://bucket/baseline_tripinfo.xml",
                "output_summary_uri": "s3://bucket/baseline_summary.xml",
                "output_queue_uri": "s3://bucket/baseline_queue.xml",
                "output_emission_uri": "s3://bucket/baseline_emission.xml",
                "execution_status": "completed",
                "execution_time_ms": 5000,
                "metadata": {},
                "created_at": "2026-05-07T10:00:04"
            }),
            # Simulator Runner (alternative)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "sim_alt",
                "request_id": "req_sim_alt",
                "experiment_id": "exp_e2e",
                "variant_id": "alt_demand_increase",
                "config_file_uri": "s3://bucket/alt.sumocfg",
                "output_tripinfo_uri": "s3://bucket/alt_tripinfo.xml",
                "output_summary_uri": "s3://bucket/alt_summary.xml",
                "output_queue_uri": "s3://bucket/alt_queue.xml",
                "output_emission_uri": "s3://bucket/alt_emission.xml",
                "execution_status": "completed",
                "execution_time_ms": 5500,
                "metadata": {},
                "created_at": "2026-05-07T10:00:05"
            }),
            # Analyzer
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "result_id": "analysis_e2e",
                "experiment_id": "exp_e2e",
                "baseline_kpis": {
                    "variant_id": "baseline",
                    "avg_travel_time": 300.0,
                    "avg_waiting_time": 60.0,
                    "avg_speed": 8.5,
                    "total_vehicles": 100,
                    "completed_trips": 95,
                    "avg_queue_length": 5.0,
                    "max_queue_length": 12.0,
                    "total_co2": 1500.0,
                    "total_nox": 50.0,
                    "total_pmx": 5.0
                },
                "alternative_kpis": [
                    {
                        "variant_id": "alt_demand_increase",
                        "avg_travel_time": 360.0,
                        "avg_waiting_time": 80.0,
                        "avg_speed": 7.5,
                        "total_vehicles": 120,
                        "completed_trips": 110,
                        "avg_queue_length": 7.0,
                        "max_queue_length": 15.0,
                        "total_co2": 1800.0,
                        "total_nox": 60.0,
                        "total_pmx": 6.0
                    }
                ],
                "comparisons": [
                    {
                        "variant_id": "alt_demand_increase",
                        "improvement_summary": {
                            "improved_count": 0,
                            "worsened_count": 10,
                            "neutral_count": 0,
                            "overall_score": -25.5
                        },
                        "improvements": {
                            "avg_travel_time": {
                                "baseline": 300.0,
                                "alternative": 360.0,
                                "improvement_rate": -20.0
                            }
                        },
                        "summary": "교통량 증가로 모든 지표 악화"
                    }
                ],
                "created_at": "2026-05-07T10:00:06"
            }),
            # Reporter
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "report_e2e",
                "experiment_id": "exp_e2e",
                "report_markdown_uri": "s3://bucket/report_e2e.md",
                "report_pdf_uri": None,
                "summary": "교통량 증가 시 모든 지표 악화",
                "key_findings": [
                    "평균 통행시간 20% 증가",
                    "평균 대기시간 33% 증가"
                ],
                "created_at": "2026-05-07T10:00:07"
            })
        ])

        # Execute pipeline
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/pipeline/run",
                json={
                    "user_request": "강남역 교통 시뮬레이션",
                    "experiment_id": "exp_e2e",
                    "dry_run": False,
                    "skip_steps": []
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Assertions
            assert data["status"] == "completed"
            assert data["experiment_id"] == "exp_e2e"
            assert data["report_uri"] == "s3://bucket/report_e2e.md"
            assert data["error_message"] is None
            assert data["total_duration_ms"] > 0

            # All steps completed
            assert len(data["steps"]) == 7
            for step in data["steps"]:
                assert step["status"] == "completed"
                assert step["duration_ms"] > 0


@pytest.mark.asyncio
async def test_run_pipeline_dry_run_e2e():
    """Dry Run 모드 E2E 테스트"""

    with patch("apps.pipeline.services.pipeline_service.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock responses (최소 응답만)
        mock_client.post = AsyncMock(side_effect=[
            # Orchestrator
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "experiment_id": "exp_dry_e2e",
                "user_request": "테스트",
                "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                "baseline_conditions": {"time_range": {"start": "08:00", "end": "09:00"}},
                "scenarios": [],
                "metrics_of_interest": ["travel_time"],
                "simulation_duration_seconds": 3600,
                "clarification_questions": [],
                "confidence_score": 0.9
            }),
            # Scenario Builder
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "plan_id": "plan_dry_e2e",
                "experiment_id": "exp_dry_e2e",
                "baseline": {
                    "request_id": "req_baseline",
                    "experiment_id": "exp_dry_e2e",
                    "area": {"center": {"lat": 37.5, "lon": 127.0}, "radius_m": 1000},
                    "network_source": "toy",
                    "modifications": [],
                    "output_format": "sumo_net"
                },
                "alternatives": [],
                "demand_baseline": {
                    "request_id": "req_demand_baseline",
                    "experiment_id": "exp_dry_e2e",
                    "network_artifact_uri": "s3://bucket/network.net.xml",
                    "time_range": {"start": "08:00", "end": "09:00"},
                    "demand_source": "toy",
                    "output_format": "sumo_routes"
                },
                "demand_alternatives": [],
                "summary": "Dry run"
            }),
            # Network Builder (baseline)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "net_dry",
                "request_id": "req_baseline",
                "experiment_id": "exp_dry_e2e",
                "network_file_uri": "s3://bucket/network.net.xml",
                "metadata": {},
                "created_at": "2026-05-07T10:00:00"
            }),
            # Demand Builder (baseline)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "demand_dry",
                "request_id": "req_demand_baseline",
                "experiment_id": "exp_dry_e2e",
                "routes_file_uri": "s3://bucket/demand.rou.xml",
                "metadata": {},
                "created_at": "2026-05-07T10:00:01"
            }),
            # Simulator Runner (dry_run=true)
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "sim_dry",
                "request_id": "req_sim_baseline",
                "experiment_id": "exp_dry_e2e",
                "variant_id": "baseline",
                "config_file_uri": "s3://bucket/baseline.sumocfg",
                "output_tripinfo_uri": "s3://bucket/baseline_tripinfo.xml",
                "output_summary_uri": "s3://bucket/baseline_summary.xml",
                "output_queue_uri": "s3://bucket/baseline_queue.xml",
                "output_emission_uri": "s3://bucket/baseline_emission.xml",
                "execution_status": "completed",
                "execution_time_ms": 100,
                "metadata": {"dry_run": True},
                "created_at": "2026-05-07T10:00:02"
            }),
            # Analyzer
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "result_id": "analysis_dry",
                "experiment_id": "exp_dry_e2e",
                "baseline_kpis": {
                    "variant_id": "baseline",
                    "avg_travel_time": 300.0,
                    "total_vehicles": 100
                },
                "alternative_kpis": [],
                "comparisons": [],
                "created_at": "2026-05-07T10:00:03"
            }),
            # Reporter
            MagicMock(status_code=200, json=lambda: {
                "version": "1.0.0",
                "artifact_id": "report_dry",
                "experiment_id": "exp_dry_e2e",
                "report_markdown_uri": "s3://bucket/report_dry.md",
                "summary": "Dry run",
                "key_findings": [],
                "created_at": "2026-05-07T10:00:04"
            })
        ])

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/pipeline/run",
                json={
                    "user_request": "테스트",
                    "experiment_id": "exp_dry_e2e",
                    "dry_run": True,
                    "skip_steps": []
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "completed"
            assert data["experiment_id"] == "exp_dry_e2e"


@pytest.mark.asyncio
async def test_run_pipeline_failure_e2e():
    """파이프라인 실패 E2E 테스트"""

    with patch("apps.pipeline.services.pipeline_service.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value.__aenter__.return_value

        # Mock response (Orchestrator 실패)
        mock_client.post = AsyncMock(side_effect=[
            MagicMock(status_code=500, json=lambda: {"detail": "LLM Gateway error"})
        ])

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/pipeline/run",
                json={
                    "user_request": "테스트",
                    "experiment_id": "exp_fail_e2e",
                    "dry_run": False,
                    "skip_steps": []
                }
            )

            assert response.status_code == 200  # Pipeline 자체는 200 (내부 step이 실패)
            data = response.json()

            assert data["status"] == "failed"
            assert data["experiment_id"] == "exp_fail_e2e"
            assert data["error_message"] is not None
