#!/usr/bin/env bash
# ============================================================================
# verify-structure.sh
# 책임: 프로젝트 구조 및 필수 파일 존재 확인
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================"
echo "프로젝트 구조 검증"
echo "============================================"
echo ""

MISSING_FILES=()
EXISTING_FILES=()

# 필수 파일 목록
REQUIRED_FILES=(
  # 루트
  "CLAUDE.md"
  "README.md"

  # Apps
  "apps/api-service/main.py"
  "apps/api-service/Dockerfile"
  "apps/api-service/requirements.txt"

  "apps/agent-service/main.py"
  "apps/agent-service/Dockerfile"
  "apps/agent-service/requirements.txt"

  "apps/simulation-service/main.py"
  "apps/simulation-service/Dockerfile"
  "apps/simulation-service/requirements.txt"

  "apps/analysis-service/main.py"
  "apps/analysis-service/Dockerfile"
  "apps/analysis-service/requirements.txt"

  "apps/report-service/main.py"
  "apps/report-service/Dockerfile"
  "apps/report-service/requirements.txt"

  "apps/frontend/src/App.jsx"
  "apps/frontend/Dockerfile"
  "apps/frontend/package.json"
  "apps/frontend/nginx.conf"

  # Helm Charts
  "infra/helm/services/api-service/Chart.yaml"
  "infra/helm/services/api-service/values.yaml"
  "infra/helm/services/api-service/values-dev.yaml"

  "infra/helm/gateway/Chart.yaml"
  "infra/helm/gateway/values.yaml"

  # Argo CD
  "infra/argocd/applications/dev/api-service.yaml"
  "infra/argocd/applications/dev/gateway.yaml"
  "infra/argocd/applicationsets/services-dev.yaml"

  # Terraform
  "infra/terraform/modules/eks/main.tf"
  "infra/terraform/modules/iam-irsa/main.tf"
  "infra/terraform/modules/vpc/main.tf"

  # Scripts
  "scripts/check-env.sh"
  "scripts/bootstrap-dev.sh"
  "scripts/terraform-dev.sh"
  "scripts/sync-kubeconfig.sh"
  "scripts/install-platform.sh"
  "scripts/register-argocd-apps.sh"
  "scripts/test-services-local.sh"

  # GitHub Actions
  ".github/workflows/build-and-push.yml"
  ".github/workflows/ci-api-service.yml"

  # Docs
  "docs/eks.md"
  "docs/gitops.md"
  "docs/cicd.md"
  "docs/services.md"
  "docs/rebuild-environment.md"
)

echo "📋 필수 파일 확인..."
echo ""

for FILE in "${REQUIRED_FILES[@]}"; do
  FULL_PATH="$PROJECT_ROOT/$FILE"

  if [ -f "$FULL_PATH" ]; then
    EXISTING_FILES+=("$FILE")
  else
    echo -e "${RED}✗${NC} $FILE"
    MISSING_FILES+=("$FILE")
  fi
done

echo ""

# 결과 요약
echo "============================================"
echo "검증 결과"
echo "============================================"
echo ""

TOTAL=${#REQUIRED_FILES[@]}
EXISTING=${#EXISTING_FILES[@]}
MISSING=${#MISSING_FILES[@]}

echo "전체: $TOTAL 파일"
echo -e "${GREEN}존재: $EXISTING 파일${NC}"

if [ $MISSING -gt 0 ]; then
  echo -e "${RED}누락: $MISSING 파일${NC}"
  echo ""
  echo "누락된 파일:"
  for FILE in "${MISSING_FILES[@]}"; do
    echo "  - $FILE"
  done
  echo ""
  exit 1
else
  echo -e "${GREEN}누락: 0 파일${NC}"
fi

echo ""

# 추가 검증
echo "============================================"
echo "추가 검증"
echo "============================================"
echo ""

# 1. 실행 권한 확인
echo "🔐 스크립트 실행 권한..."
SCRIPTS=(
  "scripts/check-env.sh"
  "scripts/bootstrap-dev.sh"
  "scripts/terraform-dev.sh"
  "scripts/sync-kubeconfig.sh"
  "scripts/install-platform.sh"
  "scripts/register-argocd-apps.sh"
  "scripts/test-services-local.sh"
)

NO_EXEC=()
for SCRIPT in "${SCRIPTS[@]}"; do
  if [ ! -x "$PROJECT_ROOT/$SCRIPT" ]; then
    NO_EXEC+=("$SCRIPT")
  fi
done

if [ ${#NO_EXEC[@]} -eq 0 ]; then
  echo -e "${GREEN}✓${NC} 모든 스크립트 실행 가능"
else
  echo -e "${YELLOW}⚠${NC} 실행 권한 없음:"
  for SCRIPT in "${NO_EXEC[@]}"; do
    echo "  - $SCRIPT"
  done
  echo ""
  echo "수정: chmod +x $PROJECT_ROOT/scripts/*.sh"
fi

echo ""

# 2. Dockerfile 문법 확인
echo "🐳 Dockerfile 문법 확인..."

DOCKERFILES=(
  "apps/api-service/Dockerfile"
  "apps/agent-service/Dockerfile"
  "apps/simulation-service/Dockerfile"
  "apps/analysis-service/Dockerfile"
  "apps/report-service/Dockerfile"
  "apps/frontend/Dockerfile"
)

INVALID_DOCKERFILES=()
for DOCKERFILE in "${DOCKERFILES[@]}"; do
  if ! grep -q "^FROM" "$PROJECT_ROOT/$DOCKERFILE" 2>/dev/null; then
    INVALID_DOCKERFILES+=("$DOCKERFILE")
  fi
done

if [ ${#INVALID_DOCKERFILES[@]} -eq 0 ]; then
  echo -e "${GREEN}✓${NC} 모든 Dockerfile 유효"
else
  echo -e "${RED}✗${NC} 잘못된 Dockerfile:"
  for DOCKERFILE in "${INVALID_DOCKERFILES[@]}"; do
    echo "  - $DOCKERFILE"
  done
fi

echo ""

# 3. Health check 엔드포인트 확인
echo "💊 Health check 엔드포인트..."

PYTHON_SERVICES=(
  "apps/api-service/main.py"
  "apps/agent-service/main.py"
  "apps/simulation-service/main.py"
  "apps/analysis-service/main.py"
  "apps/report-service/main.py"
)

NO_HEALTH=()
for SERVICE_FILE in "${PYTHON_SERVICES[@]}"; do
  if ! grep -q "/health" "$PROJECT_ROOT/$SERVICE_FILE" 2>/dev/null; then
    NO_HEALTH+=("$SERVICE_FILE")
  fi
done

if [ ${#NO_HEALTH[@]} -eq 0 ]; then
  echo -e "${GREEN}✓${NC} 모든 서비스에 /health 엔드포인트 존재"
else
  echo -e "${RED}✗${NC} /health 없음:"
  for SERVICE_FILE in "${NO_HEALTH[@]}"; do
    echo "  - $SERVICE_FILE"
  done
fi

echo ""

# 최종 결과
echo "============================================"
echo "최종 결과"
echo "============================================"
echo ""

if [ $MISSING -eq 0 ] && [ ${#NO_EXEC[@]} -eq 0 ] && [ ${#INVALID_DOCKERFILES[@]} -eq 0 ] && [ ${#NO_HEALTH[@]} -eq 0 ]; then
  echo -e "${GREEN}✓ 프로젝트 구조 검증 완료!${NC}"
  echo ""
  echo "다음 단계:"
  echo "  1. 로컬 테스트: ./scripts/test-services-local.sh"
  echo "  2. Git commit & push"
  echo "  3. 인프라 배포: ./scripts/bootstrap-dev.sh"
  exit 0
else
  echo -e "${YELLOW}⚠ 일부 검증 실패${NC}"
  echo ""
  echo "수정 후 다시 실행하세요."
  exit 1
fi
