#!/usr/bin/env bash
# ============================================================================
# bootstrap-dev.sh
# 책임: 새 컴퓨터에서 Agent T dev 환경 전체 구성 자동화
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Checkpoint 파일 경로
CHECKPOINT_FILE="${PROJECT_ROOT}/.bootstrap-checkpoint"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# 환경 변수
export ENV="dev"
export AWS_REGION="ap-northeast-2"

# ============================================================================
# Checkpoint 함수
# ============================================================================

save_checkpoint() {
  local step=$1
  echo "$step" > "$CHECKPOINT_FILE"
  echo -e "${GREEN}✓ Checkpoint 저장: Step $step${NC}"
}

get_checkpoint() {
  if [ -f "$CHECKPOINT_FILE" ]; then
    cat "$CHECKPOINT_FILE"
  else
    echo "0"
  fi
}

clear_checkpoint() {
  if [ -f "$CHECKPOINT_FILE" ]; then
    rm "$CHECKPOINT_FILE"
    echo -e "${GREEN}✓ Checkpoint 초기화${NC}"
  fi
}

echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  Agent T Bootstrap - Dev Environment${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""

# 이전 checkpoint 확인
LAST_STEP=$(get_checkpoint)

if [ "$LAST_STEP" != "0" ]; then
  echo -e "${YELLOW}이전 실행이 Step $LAST_STEP에서 중단되었습니다.${NC}"
  echo ""
  echo "옵션:"
  echo "  1) Step $((LAST_STEP + 1))부터 계속 (추천)"
  echo "  2) 처음부터 다시 시작"
  echo ""
  read -p "선택 (1/2): " RESUME_CHOICE || RESUME_CHOICE="1"

  if [ "${RESUME_CHOICE:-1}" == "2" ]; then
    clear_checkpoint
    LAST_STEP=0
    echo -e "${BLUE}처음부터 다시 시작합니다.${NC}"
  else
    echo -e "${BLUE}Step $((LAST_STEP + 1))부터 계속합니다.${NC}"
  fi
  echo ""
fi

if [ "$LAST_STEP" == "0" ]; then
  echo "이 스크립트는 새 컴퓨터에서 Agent T 개발 환경을"
  echo "처음부터 끝까지 자동으로 구성합니다."
  echo ""
  echo -e "${YELLOW}⚠ 주의: AWS 리소스 생성으로 비용이 발생합니다 (~\$150-200/월)${NC}"
  echo ""

  read -p "계속하시겠습니까? (yes/no): " CONFIRM || CONFIRM="no"
  if [ "${CONFIRM:-no}" != "yes" ]; then
    echo "취소되었습니다."
    exit 0
  fi
  echo ""
fi

# ============================================================================
# Step 1: 환경 확인
# ============================================================================

if [ "$LAST_STEP" -lt 1 ]; then
  echo -e "${BLUE}============================================${NC}"
  echo -e "${BLUE}Step 1/5: 환경 확인${NC}"
  echo -e "${BLUE}============================================${NC}"
  echo ""

  if ! "$SCRIPT_DIR/check-env.sh"; then
    echo ""
    echo -e "${RED}✗ 환경 확인 실패${NC}"
    echo "  필수 도구를 먼저 설치하세요."
    echo "  가이드: DEPLOYMENT.md"
    echo ""
    echo "재시작: ./scripts/bootstrap-dev.sh"
    exit 1
  fi

  save_checkpoint 1
  echo ""
  read -p "계속하려면 Enter를 누르세요..."
  echo ""
else
  echo -e "${GREEN}✓ Step 1/5 건너뜀 (이미 완료)${NC}"
  echo ""
fi

# ============================================================================
# Step 2: Terraform 인프라 구성
# ============================================================================

if [ "$LAST_STEP" -lt 2 ]; then
  echo -e "${BLUE}============================================${NC}"
  echo -e "${BLUE}Step 2/5: Terraform 인프라 구성${NC}"
  echo -e "${BLUE}============================================${NC}"
  echo ""
  echo "다음 리소스가 생성됩니다:"
  echo "  - VPC, Subnets, NAT Gateway"
  echo "  - EKS Cluster + Node Groups"
  echo "  - RDS PostgreSQL"
  echo "  - ElastiCache Redis"
  echo "  - S3 Buckets"
  echo "  - ECR Repositories"
  echo "  - Secrets Manager"
  echo "  - IAM Roles (IRSA)"
  echo ""

  if ! "$SCRIPT_DIR/terraform-dev.sh"; then
    echo ""
    echo -e "${RED}✗ Terraform 실행 실패${NC}"
    echo ""
    echo "재시작: ./scripts/bootstrap-dev.sh"
    exit 1
  fi

  save_checkpoint 2
  echo ""
  read -p "계속하려면 Enter를 누르세요..."
  echo ""
else
  echo -e "${GREEN}✓ Step 2/5 건너뜀 (이미 완료)${NC}"
  echo ""
fi

# ============================================================================
# Step 3: Kubeconfig 동기화
# ============================================================================

if [ "$LAST_STEP" -lt 3 ]; then
  echo -e "${BLUE}============================================${NC}"
  echo -e "${BLUE}Step 3/5: Kubeconfig 동기화${NC}"
  echo -e "${BLUE}============================================${NC}"
  echo ""

  if ! "$SCRIPT_DIR/sync-kubeconfig.sh"; then
    echo ""
    echo -e "${RED}✗ Kubeconfig 동기화 실패${NC}"
    echo ""
    echo "재시작: ./scripts/bootstrap-dev.sh"
    exit 1
  fi

  save_checkpoint 3
  echo ""
  read -p "계속하려면 Enter를 누르세요..."
  echo ""
else
  echo -e "${GREEN}✓ Step 3/5 건너뜀 (이미 완료)${NC}"
  echo ""
fi

# ============================================================================
# Step 4: 플랫폼 컴포넌트 설치
# ============================================================================

if [ "$LAST_STEP" -lt 4 ]; then
  echo -e "${BLUE}============================================${NC}"
  echo -e "${BLUE}Step 4/5: 플랫폼 컴포넌트 설치${NC}"
  echo -e "${BLUE}============================================${NC}"
  echo ""
  echo "다음 컴포넌트가 설치됩니다:"
  echo "  - AWS Load Balancer Controller"
  echo "  - Argo CD"
  echo ""

  if ! "$SCRIPT_DIR/install-platform.sh" dev all; then
    echo ""
    echo -e "${RED}✗ 플랫폼 설치 실패${NC}"
    echo ""
    echo "재시작: ./scripts/bootstrap-dev.sh"
    exit 1
  fi

  save_checkpoint 4
  echo ""
  read -p "계속하려면 Enter를 누르세요..."
  echo ""
else
  echo -e "${GREEN}✓ Step 4/5 건너뜀 (이미 완료)${NC}"
  echo ""
fi

# ============================================================================
# Step 5: Argo CD Applications 등록
# ============================================================================

if [ "$LAST_STEP" -lt 5 ]; then
  echo -e "${BLUE}============================================${NC}"
  echo -e "${BLUE}Step 5/5: Argo CD Applications 등록${NC}"
  echo -e "${BLUE}============================================${NC}"
  echo ""

  if ! "$SCRIPT_DIR/register-argocd-apps.sh"; then
    echo ""
    echo -e "${RED}✗ Applications 등록 실패${NC}"
    echo ""
    echo "재시작: ./scripts/bootstrap-dev.sh"
    exit 1
  fi

  save_checkpoint 5
  echo ""
else
  echo -e "${GREEN}✓ Step 5/5 건너뜀 (이미 완료)${NC}"
  echo ""
fi

# ============================================================================
# 완료
# ============================================================================

clear_checkpoint

echo ""
echo -e "${GREEN}${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  ✓ Bootstrap 완료!${NC}"
echo -e "${GREEN}${BOLD}============================================${NC}"
echo ""
echo "Agent T Dev 환경이 성공적으로 구성되었습니다."
echo ""
echo -e "${BOLD}다음 단계:${NC}"
echo ""
echo "1. Argo CD UI 접속:"
echo "   kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo "   https://localhost:8080"
echo ""
echo "2. Argo CD 초기 비밀번호:"
echo "   kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
echo ""
echo "3. 클러스터 상태 확인:"
echo "   kubectl get nodes"
echo "   kubectl get pods -A"
echo ""
echo "4. Argo CD Applications 확인:"
echo "   kubectl get applications -n argocd"
echo ""
echo "5. 서비스 배포 확인:"
echo "   kubectl get pods"
echo "   kubectl get ingress"
echo ""
echo -e "${YELLOW}📖 자세한 사용법:${NC}"
echo "   docs/gitops.md"
echo "   docs/platform-components.md"
echo "   docs/eks.md"
echo ""

