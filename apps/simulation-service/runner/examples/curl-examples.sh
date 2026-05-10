#!/bin/bash

# Simulator Runner API 테스트 스크립트
# 사용법: bash curl-examples.sh

BASE_URL="http://localhost:8004"

echo "=== Simulator Runner API 테스트 ==="
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

# 4. Run Simulation (Basic)
echo "4. Run Simulation - 기본 설정"
curl -X POST "${BASE_URL}/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_run_request": {
      "schema_version": "1.0",
      "request_id": "req-sim-001",
      "experiment_id": "exp-sim-001",
      "variant_id": "baseline",
      "network_artifact": {
        "schema_version": "1.0",
        "artifact_id": "net-001",
        "uri": "local:///tmp/networks/exp-sim-001/baseline/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 50000
      },
      "demand_artifact": {
        "schema_version": "1.0",
        "artifact_id": "dem-001",
        "uri": "local:///tmp/demands/exp-sim-001/baseline/routes.rou.xml",
        "file_format": "rou.xml",
        "file_size_bytes": 12000
      }
    }
  }' | jq .
echo ""
echo ""

# 5. Run Simulation with Custom Settings
echo "5. Run Simulation - 사용자 정의 설정"
curl -X POST "${BASE_URL}/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_run_request": {
      "schema_version": "1.0",
      "request_id": "req-sim-002",
      "experiment_id": "exp-sim-002",
      "variant_id": "alternative",
      "network_artifact": {
        "schema_version": "1.0",
        "artifact_id": "net-002",
        "uri": "local:///tmp/networks/exp-sim-002/alternative/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 55000
      },
      "demand_artifact": {
        "schema_version": "1.0",
        "artifact_id": "dem-002",
        "uri": "local:///tmp/demands/exp-sim-002/alternative/routes.rou.xml",
        "file_format": "rou.xml",
        "file_size_bytes": 15000
      },
      "simulation_settings": {
        "begin": 0,
        "end": 3600,
        "step_length": 1.0,
        "collision_action": "warn",
        "time_to_teleport": 300
      }
    }
  }' | jq .
echo ""
echo ""

# 6. Run Simulation with Short Duration
echo "6. Run Simulation - 짧은 시뮬레이션 (1시간)"
curl -X POST "${BASE_URL}/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_run_request": {
      "schema_version": "1.0",
      "request_id": "req-sim-003",
      "experiment_id": "exp-sim-003",
      "variant_id": "baseline",
      "network_artifact": {
        "schema_version": "1.0",
        "artifact_id": "net-003",
        "uri": "local:///tmp/networks/exp-sim-003/baseline/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 45000
      },
      "demand_artifact": {
        "schema_version": "1.0",
        "artifact_id": "dem-003",
        "uri": "local:///tmp/demands/exp-sim-003/baseline/routes.rou.xml",
        "file_format": "rou.xml",
        "file_size_bytes": 10000
      },
      "simulation_settings": {
        "begin": 0,
        "end": 3600,
        "step_length": 1.0
      }
    }
  }' | jq .
echo ""
echo ""

# 7. Run Simulation with Fine Time Step
echo "7. Run Simulation - 정밀 타임스텝 (0.5초)"
curl -X POST "${BASE_URL}/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_run_request": {
      "schema_version": "1.0",
      "request_id": "req-sim-004",
      "experiment_id": "exp-sim-004",
      "variant_id": "fine_step",
      "network_artifact": {
        "schema_version": "1.0",
        "artifact_id": "net-004",
        "uri": "local:///tmp/networks/exp-sim-004/fine_step/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 50000
      },
      "demand_artifact": {
        "schema_version": "1.0",
        "artifact_id": "dem-004",
        "uri": "local:///tmp/demands/exp-sim-004/fine_step/routes.rou.xml",
        "file_format": "rou.xml",
        "file_size_bytes": 12000
      },
      "simulation_settings": {
        "begin": 0,
        "end": 1800,
        "step_length": 0.5
      }
    }
  }' | jq .
echo ""
echo ""

# 8. Run Simulation with Collision Remove
echo "8. Run Simulation - 충돌 차량 제거"
curl -X POST "${BASE_URL}/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_run_request": {
      "schema_version": "1.0",
      "request_id": "req-sim-005",
      "experiment_id": "exp-sim-005",
      "variant_id": "collision_remove",
      "network_artifact": {
        "schema_version": "1.0",
        "artifact_id": "net-005",
        "uri": "local:///tmp/networks/exp-sim-005/collision_remove/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 48000
      },
      "demand_artifact": {
        "schema_version": "1.0",
        "artifact_id": "dem-005",
        "uri": "local:///tmp/demands/exp-sim-005/collision_remove/routes.rou.xml",
        "file_format": "rou.xml",
        "file_size_bytes": 11000
      },
      "simulation_settings": {
        "begin": 0,
        "collision_action": "remove",
        "time_to_teleport": 600
      }
    }
  }' | jq .
echo ""
echo ""

# 9. Run Simulation - No End Time (until all vehicles complete)
echo "9. Run Simulation - 종료 시간 없음 (모든 차량 완료까지)"
curl -X POST "${BASE_URL}/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_run_request": {
      "schema_version": "1.0",
      "request_id": "req-sim-006",
      "experiment_id": "exp-sim-006",
      "variant_id": "no_end",
      "network_artifact": {
        "schema_version": "1.0",
        "artifact_id": "net-006",
        "uri": "local:///tmp/networks/exp-sim-006/no_end/network.net.xml",
        "file_format": "net.xml",
        "file_size_bytes": 52000
      },
      "demand_artifact": {
        "schema_version": "1.0",
        "artifact_id": "dem-006",
        "uri": "local:///tmp/demands/exp-sim-006/no_end/routes.rou.xml",
        "file_format": "rou.xml",
        "file_size_bytes": 13000
      },
      "simulation_settings": {
        "begin": 0,
        "step_length": 1.0
      }
    }
  }' | jq .
echo ""
echo ""

# 10. Invalid Request (Missing schema_version)
echo "10. Invalid Request - schema_version 누락"
curl -X POST "${BASE_URL}/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_run_request": {
      "request_id": "req-invalid-001",
      "experiment_id": "exp-invalid-001",
      "variant_id": "baseline",
      "network_artifact": {
        "uri": "local:///tmp/networks/network.net.xml"
      },
      "demand_artifact": {
        "uri": "local:///tmp/demands/routes.rou.xml"
      }
    }
  }' | jq .
echo ""
echo ""

echo "=== 테스트 완료 ==="
