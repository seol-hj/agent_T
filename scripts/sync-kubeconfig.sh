#!/usr/bin/env bash
# ============================================================================
# sync-kubeconfig.sh
# 책임: EKS 클러스터의 kubeconfig를 로컬에 동기화
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 환경 변수 기본값
ENV="${ENV:-dev}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================"
echo "EKS Kubeconfig 동기화"
echo "============================================"
echo ""
echo "Environment: $ENV"
echo "Region: $AWS_REGION"
echo ""

# Terraform outputs에서 클러스터 정보 가져오기
TERRAFORM_DIR="$PROJECT_ROOT/infra/terraform/envs/$ENV"

if [ ! -d "$TERRAFORM_DIR" ]; then
  echo -e "${RED}✗ Terraform 디렉토리가 없습니다: $TERRAFORM_DIR${NC}"
  exit 1
fi

cd "$TERRAFORM_DIR"

# Terraform state에서 cluster name 가져오기
echo "🔍 EKS 클러스터 정보 조회 중..."
echo ""

if ! terraform output &> /dev/null; then
  echo -e "${RED}✗ Terraform state가 없습니다${NC}"
  echo "  먼저 terraform apply를 실행하세요: ./scripts/terraform-dev.sh"
  exit 1
fi

CLUSTER_NAME=$(terraform output -raw cluster_name 2>/dev/null || echo "")
CLUSTER_ENDPOINT=$(terraform output -raw cluster_endpoint 2>/dev/null || echo "")

if [ -z "$CLUSTER_NAME" ]; then
  echo -e "${RED}✗ EKS 클러스터가 생성되지 않았습니다${NC}"
  echo "  먼저 terraform apply를 실행하세요: ./scripts/terraform-dev.sh"
  exit 1
fi

echo -e "${GREEN}✓${NC} 클러스터 발견: $CLUSTER_NAME"
echo "  Endpoint: $CLUSTER_ENDPOINT"
echo ""

# Kubeconfig 업데이트
echo "🔧 Kubeconfig 업데이트 중..."
echo ""

if aws eks update-kubeconfig \
    --region "$AWS_REGION" \
    --name "$CLUSTER_NAME" \
    --alias "agent-t-$ENV"; then
  echo -e "${GREEN}✓${NC} Kubeconfig 업데이트 완료"
else
  echo -e "${RED}✗${NC} Kubeconfig 업데이트 실패"
  exit 1
fi

echo ""

# 연결 확인
echo "🔌 클러스터 연결 확인..."
echo ""

if kubectl cluster-info &> /dev/null; then
  echo -e "${GREEN}✓${NC} 클러스터 연결 성공"
  echo ""
  kubectl cluster-info
else
  echo -e "${RED}✗${NC} 클러스터 연결 실패"
  exit 1
fi

echo ""

# 현재 컨텍스트 출력
echo "============================================"
echo "현재 Kubernetes 컨텍스트"
echo "============================================"
echo ""

kubectl config current-context

echo ""

# Node 상태 확인
echo "============================================"
echo "Node 상태"
echo "============================================"
echo ""

kubectl get nodes

echo ""
echo -e "${GREEN}✓ Kubeconfig 동기화 완료${NC}"
echo ""
echo "다음 단계:"
echo "  ./scripts/install-platform.sh"

