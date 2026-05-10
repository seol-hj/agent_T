#!/bin/bash
#
# Scenario Builder API 호출 예시
#

BASE_URL="http://localhost:8001"

echo "=========================================="
echo "Scenario Builder API 호출 예시"
echo "=========================================="
echo ""

# 1. Health Check
echo "1. Health Check"
echo "-------------------"
curl -s "${BASE_URL}/health" | jq .
echo ""

# 2. 교통량 증가 시나리오
echo "2. 교통량 20% 증가 시나리오"
echo "----------------------------"
curl -s -X POST "${BASE_URL}/scenario-builder/build" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_spec": {
      "experiment_id": "exp-20260507-001",
      "request_id": "req-001",
      "title": "강남구 교통량 증가 분석",
      "description": "차량 수 20% 증가 시 영향 분석",
      "location": {
        "region": "서울특별시 강남구",
        "bbox": [127.0276, 37.4959, 127.0948, 37.5219],
        "osm_query": "Gangnam-gu, Seoul, South Korea"
      },
      "time_settings": {
        "start_time": "07:00",
        "end_time": "09:00",
        "duration_hours": 2
      },
      "traffic_settings": {
        "vehicle_count": 5000,
        "vehicle_distribution": {"passenger": 0.8, "bus": 0.1, "truck": 0.1}
      },
      "objectives": ["통행 시간 분석", "혼잡도 분석"],
      "constraints": []
    },
    "request_type": "demand_increase"
  }' | jq '{
    experiment_id: .experiment_id,
    baseline_variant_id: .baseline_variant_id,
    alternative_variant_ids: .alternative_variant_ids,
    baseline_vehicle_count: .demand_requests[0].demand_settings.vehicle_count,
    alternative_vehicle_count: .demand_requests[1].demand_settings.vehicle_count,
    processing_time_ms: .processing_time_ms
  }'
echo ""

# 3. 차로 변경 시나리오
echo "3. 차로 추가 시나리오"
echo "----------------------"
curl -s -X POST "${BASE_URL}/scenario-builder/build" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_spec": {
      "experiment_id": "exp-20260507-002",
      "request_id": "req-002",
      "title": "테헤란로 차로 추가 효과",
      "description": "주요 도로 차로 1개 추가 시 영향",
      "location": {
        "region": "서울특별시 강남구 테헤란로",
        "osm_query": "Teheran-ro, Gangnam-gu, Seoul"
      },
      "time_settings": {
        "start_time": "07:00",
        "end_time": "09:00"
      },
      "traffic_settings": {
        "vehicle_count": 5000
      },
      "objectives": ["통행 시간 단축"],
      "constraints": []
    },
    "request_type": "lane_change"
  }' | jq '{
    experiment_id: .experiment_id,
    baseline_modifications: .network_requests[0].modifications,
    alternative_modifications: .network_requests[1].modifications,
    alternative_name: .scenario_plan.alternatives[0].name
  }'
echo ""

# 4. 신호 타이밍 변경 시나리오
echo "4. 신호 타이밍 최적화 시나리오"
echo "-------------------------------"
curl -s -X POST "${BASE_URL}/scenario-builder/build" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_spec": {
      "experiment_id": "exp-20260507-003",
      "request_id": "req-003",
      "title": "강남구 신호등 최적화",
      "description": "AI 기반 신호 타이밍 최적화",
      "location": {
        "region": "서울특별시 강남구",
        "bbox": [127.0276, 37.4959, 127.0948, 37.5219]
      },
      "time_settings": {
        "start_time": "07:00",
        "end_time": "09:00"
      },
      "traffic_settings": {
        "vehicle_count": 5000
      },
      "objectives": ["통행 시간 단축", "배출량 감소"],
      "constraints": []
    },
    "request_type": "signal_timing_change"
  }' | jq '{
    experiment_id: .experiment_id,
    baseline_name: .scenario_plan.baseline.name,
    alternative_name: .scenario_plan.alternatives[0].name,
    signal_modifications: .network_requests[1].modifications[0]
  }'
echo ""

# 5. 서비스 정보
echo "5. 지원 요청 타입"
echo "-----------------"
curl -s "${BASE_URL}/" | jq '.supported_request_types'
echo ""

echo "=========================================="
echo "완료"
echo "=========================================="
