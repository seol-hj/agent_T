#!/bin/bash

# Demand Builder API 테스트 스크립트
# 사용법: bash curl-examples.sh

BASE_URL="http://localhost:8003"

echo "=== Demand Builder API 테스트 ==="
echo ""

# 1. Health Check
echo "1. Health Check"
curl -X GET "${BASE_URL}/health" | jq .
echo ""
echo ""

# 2. Readiness Check
echo "2. Readiness Check"
curl -X GET "${BASE_URL}/ready" | jq .
echo ""
echo ""

# 3. Root Endpoint
echo "3. Root Endpoint (서비스 정보)"
curl -X GET "${BASE_URL}/" | jq .
echo ""
echo ""

# 4. Build Demand (Toy Provider, Single Vehicle Type)
echo "4. Build Demand - Toy Provider (단일 차종)"
curl -X POST "${BASE_URL}/demand/build" \
  -H "Content-Type: application/json" \
  -d '{
    "demand_build_request": {
      "schema_version": "1.0",
      "request_id": "req-toy-001",
      "experiment_id": "exp-toy-001",
      "variant_id": "baseline",
      "demand_settings": {
        "provider_type": "toy",
        "vehicle_count": 50,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {
          "passenger": 1.0
        },
        "trip_distribution": "random"
      }
    }
  }' | jq .
echo ""
echo ""

# 5. Build Demand (Toy Provider, Multiple Vehicle Types)
echo "5. Build Demand - Toy Provider (여러 차종)"
curl -X POST "${BASE_URL}/demand/build" \
  -H "Content-Type: application/json" \
  -d '{
    "demand_build_request": {
      "schema_version": "1.0",
      "request_id": "req-toy-002",
      "experiment_id": "exp-toy-002",
      "variant_id": "alternative",
      "demand_settings": {
        "provider_type": "toy",
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {
          "passenger": 0.7,
          "bus": 0.2,
          "truck": 0.1
        },
        "trip_distribution": "uniform"
      }
    }
  }' | jq .
echo ""
echo ""

# 6. Build Demand with Demand Multiplier
echo "6. Build Demand - Demand Multiplier (1.5배)"
curl -X POST "${BASE_URL}/demand/build" \
  -H "Content-Type: application/json" \
  -d '{
    "demand_build_request": {
      "schema_version": "1.0",
      "request_id": "req-toy-003",
      "experiment_id": "exp-toy-003",
      "variant_id": "high_demand",
      "demand_settings": {
        "provider_type": "toy",
        "vehicle_count": 150,
        "start_time": 0,
        "end_time": 7200,
        "vehicle_types": {
          "passenger": 0.8,
          "bus": 0.1,
          "truck": 0.1
        },
        "demand_multiplier": 1.5
      }
    }
  }' | jq .
echo ""
echo ""

# 7. Build Demand with Network Artifact
echo "7. Build Demand - Network Artifact 포함"
curl -X POST "${BASE_URL}/demand/build" \
  -H "Content-Type: application/json" \
  -d '{
    "demand_build_request": {
      "schema_version": "1.0",
      "request_id": "req-toy-004",
      "experiment_id": "exp-toy-004",
      "variant_id": "baseline",
      "demand_settings": {
        "provider_type": "toy",
        "vehicle_count": 80,
        "start_time": 0,
        "end_time": 1800,
        "vehicle_types": {
          "passenger": 0.9,
          "bus": 0.1
        }
      }
    },
    "network_artifact": {
      "schema_version": "1.0",
      "artifact_id": "net-toy-001",
      "uri": "local:///tmp/networks/exp-toy-004/baseline/network.net.xml",
      "file_format": "net.xml",
      "file_size_bytes": 5000
    }
  }' | jq .
echo ""
echo ""

# 8. Build Demand - Uniform Distribution
echo "8. Build Demand - Uniform 출발 시간 분포"
curl -X POST "${BASE_URL}/demand/build" \
  -H "Content-Type: application/json" \
  -d '{
    "demand_build_request": {
      "schema_version": "1.0",
      "request_id": "req-toy-005",
      "experiment_id": "exp-toy-005",
      "variant_id": "uniform",
      "demand_settings": {
        "provider_type": "toy",
        "vehicle_count": 20,
        "start_time": 0,
        "end_time": 200,
        "vehicle_types": {
          "passenger": 1.0
        },
        "trip_distribution": "uniform"
      }
    }
  }' | jq .
echo ""
echo ""

# 9. Invalid Request (Missing schema_version)
echo "9. Invalid Request - schema_version 누락"
curl -X POST "${BASE_URL}/demand/build" \
  -H "Content-Type: application/json" \
  -d '{
    "demand_build_request": {
      "request_id": "req-invalid-001",
      "experiment_id": "exp-invalid-001",
      "variant_id": "baseline",
      "demand_settings": {
        "provider_type": "toy",
        "vehicle_count": 100
      }
    }
  }' | jq .
echo ""
echo ""

# 10. Unsupported Provider
echo "10. Unsupported Provider - od_matrix (아직 미구현)"
curl -X POST "${BASE_URL}/demand/build" \
  -H "Content-Type: application/json" \
  -d '{
    "demand_build_request": {
      "schema_version": "1.0",
      "request_id": "req-od-001",
      "experiment_id": "exp-od-001",
      "variant_id": "baseline",
      "demand_settings": {
        "provider_type": "od_matrix",
        "vehicle_count": 100,
        "start_time": 0,
        "end_time": 3600,
        "vehicle_types": {
          "passenger": 1.0
        }
      }
    }
  }' | jq .
echo ""
echo ""

echo "=== 테스트 완료 ==="
