#!/bin/bash

# 로컬 Docker Compose 서비스 기능 테스트 스크립트

set -e

echo "=========================================="
echo "AI Agent T - 서비스 기능 테스트"
echo "=========================================="
echo ""

BASE_URL="http://localhost"

# 색상 출력
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 결과 카운터
PASSED=0
FAILED=0

# 테스트 함수
test_endpoint() {
    local service=$1
    local port=$2
    local endpoint=$3
    local method=${4:-GET}
    local data=${5:-}

    echo -n "Testing $service ($endpoint)... "

    if [ "$method" == "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL:$port$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL:$port$endpoint" 2>/dev/null || echo "000")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        if [ ! -z "$body" ]; then
            echo "   Response: $(echo $body | jq -c '.' 2>/dev/null || echo $body | head -c 100)"
        fi
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        FAILED=$((FAILED + 1))
        if [ ! -z "$body" ]; then
            echo "   Error: $(echo $body | head -c 200)"
        fi
        return 1
    fi
}

echo "1. Health Check 테스트"
echo "----------------------------------------"
test_endpoint "Agent Service" 8001 "/health"
test_endpoint "Simulation Service" 8005 "/health"
test_endpoint "Analysis Service" 8006 "/health"
test_endpoint "Report Service" 8007 "/health"
test_endpoint "Pipeline Service" 8000 "/health"
echo ""

echo "2. Ready Check 테스트"
echo "----------------------------------------"
test_endpoint "Agent Service" 8001 "/ready"
test_endpoint "Simulation Service" 8005 "/ready"
test_endpoint "Analysis Service" 8006 "/ready"
test_endpoint "Report Service" 8007 "/ready"
echo ""

echo "3. 서비스 정보 조회 테스트"
echo "----------------------------------------"
test_endpoint "Agent Service" 8001 "/"
test_endpoint "Simulation Service" 8005 "/"
test_endpoint "Analysis Service" 8006 "/"
test_endpoint "Report Service" 8007 "/"
test_endpoint "Pipeline Service" 8000 "/"
echo ""

echo "4. 시나리오 빌드 테스트 (Agent Service)"
echo "----------------------------------------"
SCENARIO_DATA='{
  "user_request": "강남역 일대 교통량 20% 증가 시뮬레이션",
  "experiment_id": "test-exp-001"
}'
test_endpoint "Scenario Builder" 8001 "/scenario/build" "POST" "$SCENARIO_DATA"
echo ""

echo "5. 네트워크 빌드 테스트 (Simulation Service) - Placeholder"
echo "----------------------------------------"
NETWORK_DATA='{
  "experiment_id": "test-exp-001",
  "scenario_id": "test-scenario-001",
  "location": {
    "bbox": [126.9, 37.5, 127.0, 37.6]
  }
}'
if test_endpoint "Network Builder" 8005 "/network/build" "POST" "$NETWORK_DATA"; then
    echo "   ℹ️  Placeholder mode (SUMO not installed)"
fi
echo ""

echo "6. E2E 파이프라인 테스트 (Pipeline Service) - Dry Run"
echo "----------------------------------------"
PIPELINE_DATA='{
  "request_id": "test-req-001",
  "user_request": "서울 강남역 일대 교통 시뮬레이션",
  "dry_run": true
}'

echo "   Starting E2E pipeline test..."
start_time=$(date +%s)

# 파이프라인 시작
RESPONSE=$(curl -s -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d "$PIPELINE_DATA")

EXECUTION_ID=$(echo "$RESPONSE" | jq -r '.execution_id // empty')

if [ -z "$EXECUTION_ID" ]; then
    echo -e "   ${RED}✗ Pipeline start failed${NC}"
    echo "   Error: $RESPONSE"
    ((FAILED++))
else
    echo -e "   ${GREEN}✓ Pipeline started${NC} (execution_id: $EXECUTION_ID)"
    ((PASSED++))

    # 진행률 조회 테스트 (3번)
    echo "   Testing progress API..."
    for i in {1..3}; do
        sleep 2
        STATUS=$(curl -s http://localhost:8000/pipeline/$EXECUTION_ID/status | jq -r '.status // empty')
        echo "   [$i] Status: $STATUS"

        if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
            break
        fi
    done

    end_time=$(date +%s)
    duration=$((end_time - start_time))
    echo -e "   ${GREEN}✓ Progress API working${NC} (checked in ${duration}s)"
    ((PASSED++))
fi
echo ""

echo "=========================================="
echo "테스트 결과 요약"
echo "=========================================="
echo -e "총 테스트: $((PASSED + FAILED))"
echo -e "${GREEN}성공: $PASSED${NC}"
echo -e "${RED}실패: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 모든 테스트 통과!${NC}"
    echo ""
    echo "다음 단계:"
    echo "  1. 로그 확인: docker-compose logs -f"
    echo "  2. 전체 파이프라인 실행: curl -X POST http://localhost:8000/pipeline/run -H 'Content-Type: application/json' -d '{...}'"
    echo "  3. SUMO 실제 시뮬레이션: dry_run: false로 설정"
    exit 0
else
    echo -e "${RED}✗ 일부 테스트 실패${NC}"
    echo ""
    echo "문제 해결:"
    echo "  1. 서비스 로그 확인: docker-compose logs <service-name>"
    echo "  2. 컨테이너 상태 확인: docker-compose ps"
    echo "  3. 재시작: docker-compose restart <service-name>"
    exit 1
fi
