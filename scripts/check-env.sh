#!/usr/bin/env bash
# ============================================================================
# check-env.sh
# 책임: 필수 도구 및 환경 변수 확인
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 결과 추적
MISSING_TOOLS=()
MISSING_VARS=()

echo "============================================"
echo "환경 확인 시작"
echo "============================================"
echo ""

# 1. 필수 CLI 도구 확인
echo "📦 필수 도구 확인..."
echo ""

check_tool() {
  local tool=$1
  local version_flag=${2:-"--version"}

  if command -v "$tool" &> /dev/null; then
    local version
    version=$($tool $version_flag 2>&1 | head -n1 || echo "버전 확인 실패")
    echo -e "${GREEN}✓${NC} $tool: $version"
    return 0
  else
    echo -e "${RED}✗${NC} $tool: 설치되지 않음"
    MISSING_TOOLS+=("$tool")
    return 1
  fi
}

check_tool "aws" "--version"
check_tool "terraform" "-version"
check_tool "kubectl" "version --client"
check_tool "helm" "version --short"
check_tool "docker" "--version"
check_tool "jq" "--version"
check_tool "git" "--version"

echo ""

# 2. AWS 인증 확인
echo "🔐 AWS 인증 확인..."
echo ""

if aws sts get-caller-identity &> /dev/null; then
  AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
  AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
  echo -e "${GREEN}✓${NC} AWS 인증 성공"
  echo "  Account: $AWS_ACCOUNT"
  echo "  User: $AWS_USER"
else
  echo -e "${RED}✗${NC} AWS 인증 실패"
  echo "  다음 명령으로 인증하세요: aws configure"
  MISSING_VARS+=("AWS_CREDENTIALS")
fi

echo ""

# 3. Docker 실행 확인
echo "🐳 Docker 실행 확인..."
echo ""

if docker info &> /dev/null; then
  echo -e "${GREEN}✓${NC} Docker 데몬 실행 중"
else
  echo -e "${RED}✗${NC} Docker 데몬이 실행되지 않음"
  echo "  Docker Desktop을 시작하거나 Docker 서비스를 시작하세요"
  MISSING_TOOLS+=("docker-daemon")
fi

echo ""

# 4. Git repository 확인
echo "📂 Git repository 확인..."
echo ""

if git rev-parse --is-inside-work-tree &> /dev/null; then
  CURRENT_BRANCH=$(git branch --show-current)
  REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "origin 없음")
  echo -e "${GREEN}✓${NC} Git repository 확인"
  echo "  Branch: $CURRENT_BRANCH"
  echo "  Remote: $REMOTE_URL"
else
  echo -e "${YELLOW}⚠${NC} Git repository가 아닙니다"
fi

echo ""

# 5. Terraform backend 확인 (선택 사항)
echo "🗄️  Terraform backend S3 확인..."
echo ""

BACKEND_BUCKET_DEV="agent-t-terraform-state-dev"
BACKEND_BUCKET_PROD="agent-t-terraform-state-prod"

check_s3_bucket() {
  local bucket=$1
  if aws s3 ls "s3://$bucket" &> /dev/null; then
    echo -e "${GREEN}✓${NC} $bucket 존재"
    return 0
  else
    echo -e "${YELLOW}⚠${NC} $bucket 없음 (첫 실행 시 자동 생성)"
    return 1
  fi
}

check_s3_bucket "$BACKEND_BUCKET_DEV"
check_s3_bucket "$BACKEND_BUCKET_PROD"

echo ""

# 결과 요약
echo "============================================"
echo "환경 확인 결과"
echo "============================================"
echo ""

if [ ${#MISSING_TOOLS[@]} -eq 0 ] && [ ${#MISSING_VARS[@]} -eq 0 ]; then
  echo -e "${GREEN}✓ 모든 필수 도구가 설치되어 있습니다${NC}"
  echo ""
  echo "다음 단계:"
  echo "  ./scripts/bootstrap-dev.sh"
  exit 0
else
  echo -e "${RED}✗ 일부 도구가 누락되었습니다${NC}"
  echo ""

  if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo "누락된 도구:"
    for tool in "${MISSING_TOOLS[@]}"; do
      echo "  - $tool"
    done
    echo ""
  fi

  if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "누락된 설정:"
    for var in "${MISSING_VARS[@]}"; do
      echo "  - $var"
    done
    echo ""
  fi

  echo "설치 가이드는 docs/rebuild-environment.md를 참조하세요"
  exit 1
fi
