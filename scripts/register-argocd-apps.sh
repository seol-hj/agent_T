#!/usr/bin/env bash
# ============================================================================
# register-argocd-apps.sh
# 책임: Argo CD에 Application 등록
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 환경 변수 기본값
ENV="${ENV:-dev}"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================"
echo "Argo CD Applications 등록"
echo "============================================"
echo ""
echo "Environment: $ENV"
echo ""

APPS_DIR="$PROJECT_ROOT/infra/argocd/applications/$ENV"
APPSET_DIR="$PROJECT_ROOT/infra/argocd/applicationsets"

# 디렉토리 확인
if [ ! -d "$APPS_DIR" ]; then
  echo -e "${RED}✗ Applications 디렉토리가 없습니다: $APPS_DIR${NC}"
  exit 1
fi

# Argo CD 실행 확인
echo "🔍 Argo CD 상태 확인..."
echo ""

if ! kubectl get namespace argocd &> /dev/null; then
  echo -e "${RED}✗ Argo CD가 설치되지 않았습니다${NC}"
  echo "  먼저 install-platform.sh를 실행하세요"
  exit 1
fi

if ! kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server &> /dev/null; then
  echo -e "${RED}✗ Argo CD server Pod가 없습니다${NC}"
  exit 1
fi

echo -e "${GREEN}✓${NC} Argo CD 실행 중"
echo ""

# 등록 방식 선택
echo "============================================"
echo "등록 방식 선택"
echo "============================================"
echo ""
echo "1. ApplicationSet 사용 (권장) - 모든 서비스 일괄 등록"
echo "2. 개별 Application 등록 - 서비스별 수동 등록"
echo ""

read -p "선택 (1 또는 2): " CHOICE

case $CHOICE in
  1)
    echo ""
    echo "============================================"
    echo "ApplicationSet 등록"
    echo "============================================"
    echo ""

    APPSET_FILE="$APPSET_DIR/services-$ENV.yaml"

    if [ ! -f "$APPSET_FILE" ]; then
      echo -e "${RED}✗ ApplicationSet 파일이 없습니다: $APPSET_FILE${NC}"
      exit 1
    fi

    echo "등록할 ApplicationSet:"
    echo "  $APPSET_FILE"
    echo ""

    if kubectl apply -f "$APPSET_FILE"; then
      echo -e "${GREEN}✓${NC} ApplicationSet 등록 완료"
    else
      echo -e "${RED}✗${NC} ApplicationSet 등록 실패"
      exit 1
    fi

    echo ""
    echo "생성된 Applications:"
    kubectl get applications -n argocd -l environment=$ENV
    ;;

  2)
    echo ""
    echo "============================================"
    echo "개별 Application 등록"
    echo "============================================"
    echo ""

    # Gateway 먼저 등록
    GATEWAY_FILE="$APPS_DIR/gateway.yaml"

    if [ -f "$GATEWAY_FILE" ]; then
      echo "🌐 Gateway 등록 중..."
      if kubectl apply -f "$GATEWAY_FILE"; then
        echo -e "${GREEN}✓${NC} Gateway 등록 완료"
      else
        echo -e "${RED}✗${NC} Gateway 등록 실패"
      fi
      echo ""
    fi

    # 각 서비스 등록
    SERVICES=(
      "api-service"
      "agent-service"
      "simulation-service"
      "analysis-service"
      "report-service"
      "frontend"
    )

    for SERVICE in "${SERVICES[@]}"; do
      APP_FILE="$APPS_DIR/$SERVICE.yaml"

      if [ ! -f "$APP_FILE" ]; then
        echo -e "${YELLOW}⚠${NC} $SERVICE: 파일 없음, 건너뜀"
        continue
      fi

      echo "📦 $SERVICE 등록 중..."

      if kubectl apply -f "$APP_FILE"; then
        echo -e "${GREEN}✓${NC} $SERVICE 등록 완료"
      else
        echo -e "${RED}✗${NC} $SERVICE 등록 실패"
      fi

      echo ""
    done
    ;;

  *)
    echo -e "${RED}✗ 잘못된 선택입니다${NC}"
    exit 1
    ;;
esac

echo ""

# 동기화 상태 대기
echo "============================================"
echo "동기화 대기 (최대 2분)"
echo "============================================"
echo ""

echo "Argo CD가 Git repository에서 Helm Charts를 동기화합니다..."
echo "이 과정은 수 분이 걸릴 수 있습니다."
echo ""

sleep 10

# Application 상태 확인
echo "Application 상태:"
kubectl get applications -n argocd -l environment=$ENV

echo ""

# 동기화 상태 확인
echo "============================================"
echo "상세 상태 확인"
echo "============================================"
echo ""

if command -v argocd &> /dev/null; then
  echo "Argo CD CLI로 상세 상태 확인:"
  echo ""
  argocd app list
else
  echo -e "${YELLOW}⚠${NC} Argo CD CLI가 설치되지 않았습니다"
  echo "  설치: brew install argocd (macOS) 또는 https://argo-cd.readthedocs.io/en/stable/cli_installation/"
fi

echo ""
echo -e "${GREEN}✓ Argo CD Applications 등록 완료${NC}"
echo ""
echo "다음 단계:"
echo "  1. Argo CD UI 접속:"
echo "     kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo "     https://localhost:8080"
echo ""
echo "  2. 초기 비밀번호 확인:"
echo "     kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
echo ""
echo "  3. Application 동기화 확인:"
echo "     argocd app list"
echo "     argocd app get <app-name>"
echo ""
echo "  4. 문제 발생 시:"
echo "     kubectl get applications -n argocd"
echo "     kubectl describe application <app-name> -n argocd"
