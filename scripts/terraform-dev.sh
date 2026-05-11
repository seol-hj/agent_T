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

# AWS 리전 설정 (Terraform backend가 ap-northeast-2에 있음)
export AWS_REGION=ap-northeast-2

# AWS 자격 증명이 환경 변수에 있으면 유지, 없으면 기본 프로파일 사용
# 환경 변수가 우선순위가 높으므로 명시적으로 설정하지 않음
# (AWS CLI와 Terraform이 자동으로 credentials 파일 또는 환경 변수 사용)

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

# 디버깅: 현재 환경 변수 출력
echo -e "${BLUE}현재 AWS 설정:${NC}"
echo "  AWS_REGION: ${AWS_REGION:-not set}"
echo "  AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-not set}"
echo "  AWS Identity: $(aws sts get-caller-identity --query Arn --output text 2>/dev/null || echo 'Failed to get identity')"
echo ""

# 이전 상태 정리 (IAM 정책 변경 등으로 캐시가 오래된 경우)
if [ -d ".terraform" ] || [ -f ".terraform.lock.hcl" ]; then
  echo -e "${YELLOW}⚠ 이전 Terraform 캐시 발견. 정리 중...${NC}"
  rm -rf .terraform .terraform.lock.hcl terraform.tfstate terraform.tfstate.backup
  echo ""
fi

# S3 접근 테스트
echo -e "${BLUE}S3 백엔드 접근 테스트...${NC}"
if aws s3 ls s3://agent-t-terraform-state-dev/ 2>&1; then
  echo -e "${GREEN}✓ S3 버킷 접근 성공${NC}"
else
  echo -e "${RED}✗ S3 버킷 접근 실패${NC}"
  echo "IAM 권한을 확인하세요."
  exit 1
fi
echo ""

if terraform init -reconfigure; then
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
echo -e "${YELLOW}예상 비용: ~\$150-200/월 (dev 환경)${NC}"
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
