#!/usr/bin/env bash
# ============================================================================
# terraform-dev.sh
# 책임: dev 환경 Terraform 초기화 및 적용
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/infra/terraform/envs/dev"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================"
echo "Terraform Dev 환경 구성"
echo "============================================"
echo ""

# Terraform 디렉토리 확인
if [ ! -d "$TERRAFORM_DIR" ]; then
  echo -e "${RED}✗ Terraform 디렉토리가 없습니다: $TERRAFORM_DIR${NC}"
  exit 1
fi

cd "$TERRAFORM_DIR"

echo -e "${BLUE}📁 작업 디렉토리: $TERRAFORM_DIR${NC}"
echo ""

# 1. Terraform 초기화
echo "============================================"
echo "1. Terraform 초기화"
echo "============================================"
echo ""

if terraform init; then
  echo -e "${GREEN}✓ Terraform 초기화 완료${NC}"
else
  echo -e "${RED}✗ Terraform 초기화 실패${NC}"
  exit 1
fi

echo ""

# 2. Terraform Plan
echo "============================================"
echo "2. Terraform Plan"
echo "============================================"
echo ""

if terraform plan -out=tfplan; then
  echo -e "${GREEN}✓ Terraform Plan 생성 완료${NC}"
else
  echo -e "${RED}✗ Terraform Plan 생성 실패${NC}"
  exit 1
fi

echo ""

# 3. 승인 대기
echo "============================================"
echo "3. 승인 대기"
echo "============================================"
echo ""

echo -e "${YELLOW}⚠ 위 Plan을 확인하고 계속 진행하시겠습니까?${NC}"
echo ""
echo "생성될 리소스:"
echo "  - VPC (Subnets, NAT Gateway, IGW)"
echo "  - EKS Cluster (Control Plane + Node Groups)"
echo "  - RDS PostgreSQL"
echo "  - ElastiCache Redis"
echo "  - S3 Buckets"
echo "  - ECR Repositories"
echo "  - Secrets Manager"
echo "  - IAM Roles (IRSA)"
echo ""
echo -e "${YELLOW}예상 비용: ~$150-200/월 (dev 환경)${NC}"
echo ""

read -p "계속하시겠습니까? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo -e "${YELLOW}✗ 사용자가 취소했습니다${NC}"
  echo ""
  echo "Plan 파일은 저장되었습니다: tfplan"
  echo "나중에 적용하려면: cd $TERRAFORM_DIR && terraform apply tfplan"
  exit 0
fi

echo ""

# 4. Terraform Apply
echo "============================================"
echo "4. Terraform Apply"
echo "============================================"
echo ""

if terraform apply tfplan; then
  echo -e "${GREEN}✓ Terraform Apply 완료${NC}"
else
  echo -e "${RED}✗ Terraform Apply 실패${NC}"
  exit 1
fi

echo ""

# 5. Output 출력
echo "============================================"
echo "5. 리소스 정보 출력"
echo "============================================"
echo ""

terraform output

echo ""
echo -e "${GREEN}✓ Dev 환경 구성 완료${NC}"
echo ""
echo "다음 단계:"
echo "  1. Kubeconfig 동기화: ./scripts/sync-kubeconfig.sh"
echo "  2. 플랫폼 설치: ./scripts/install-platform.sh"
echo "  3. Argo CD Applications 등록: ./scripts/register-argocd-apps.sh"
