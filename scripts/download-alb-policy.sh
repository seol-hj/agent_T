#!/usr/bin/env bash
# ============================================================================
# download-alb-policy.sh
# 책임: AWS Load Balancer Controller IAM Policy 다운로드
#
# 사용법:
#   ./scripts/download-alb-policy.sh [output-dir]
#
# 인자:
#   output-dir - 저장 디렉토리 (기본값: infra/terraform/envs/policies/)
# ============================================================================

set -euo pipefail

# ==== 색상 정의 ==============================================================
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# ==== 디렉토리 설정 ==========================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

OUTPUT_DIR="${1:-$PROJECT_ROOT/infra/terraform/policies}"
OUTPUT_FILE="$OUTPUT_DIR/alb-controller-policy.json"

log_info "Output directory: $OUTPUT_DIR"
log_info "Output file: $OUTPUT_FILE"

# ==== 디렉토리 생성 ==========================================================
mkdir -p "$OUTPUT_DIR"

# ==== IAM Policy 다운로드 ====================================================
log_info "Downloading AWS Load Balancer Controller IAM Policy..."

curl -sSL -o "$OUTPUT_FILE" \
    https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

if [ $? -eq 0 ]; then
    log_success "IAM Policy downloaded successfully."
    log_info "File: $OUTPUT_FILE"
else
    echo "Failed to download IAM Policy."
    exit 1
fi

# ==== 확인 ==================================================================
log_info "Policy preview:"
head -n 20 "$OUTPUT_FILE"

echo ""
log_success "Done!"
log_info "Use this policy in Terraform:"
echo ""
echo "resource \"aws_iam_policy\" \"alb_controller\" {"
echo "  name        = \"\${var.project_name}-\${var.env}-alb-controller-policy\""
echo "  description = \"IAM policy for AWS Load Balancer Controller\""
echo "  policy      = file(\"\${path.module}/../policies/alb-controller-policy.json\")"
echo "}"
