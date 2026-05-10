#!/bin/bash
#
# Orchestrator API 호출 예시
#

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Orchestrator API 호출 예시"
echo "=========================================="
echo ""

# 1. Health Check
echo "1. Health Check"
echo "-------------------"
curl -s "${BASE_URL}/health" | jq .
echo ""

# 2. 신호 타이밍 변경 요청 (성공 예상)
echo "2. 신호 타이밍 변경 요청"
echo "-------------------------"
curl -s -X POST "${BASE_URL}/orchestrator/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "서울 강남구 출퇴근 시간대(07:00-09:00) 교통량을 분석하고 신호등 최적화 효과를 비교하고 싶습니다",
    "user_id": "user-001"
  }' | jq .
echo ""

# 3. 정보 부족 요청 (보완 질문 예상)
echo "3. 정보 부족 요청 (보완 질문 기대)"
echo "------------------------------------"
curl -s -X POST "${BASE_URL}/orchestrator/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "교통량이 증가하면 어떻게 될까요?",
    "user_id": "user-001"
  }' | jq .
echo ""

# 4. RAG 컨텍스트 포함 요청
echo "4. RAG 컨텍스트 포함 요청"
echo "-------------------------"
curl -s -X POST "${BASE_URL}/orchestrator/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "테헤란로에 차로를 추가하면 어떻게 될까요?",
    "user_id": "user-001",
    "rag_contexts": [
      {
        "context_type": "previous_experiment",
        "content": "이전 실험에서 강남구 테헤란로를 분석했습니다. 현재 3차로이며 평일 아침 교통량이 매우 높습니다.",
        "relevance_score": 0.85,
        "source": "exp-20260501-001"
      }
    ]
  }' | jq .
echo ""

# 5. 교통량 증가 시나리오
echo "5. 교통량 증가 시나리오"
echo "-----------------------"
curl -s -X POST "${BASE_URL}/orchestrator/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "부산 해운대구에서 차량이 30% 증가한다고 가정하고 주말 낮 시간대(10:00-18:00)에 교통 혼잡도를 분석하고 싶습니다",
    "user_id": "user-002"
  }' | jq .
echo ""

# 6. 로그 조회
echo "6. 로그 조회 (최근 10개)"
echo "------------------------"
curl -s "${BASE_URL}/orchestrator/logs?limit=10" | jq .
echo ""

echo "=========================================="
echo "완료"
echo "=========================================="
