#!/usr/bin/env bash
# ============================================================================
# install-platform.sh
# 책임: EKS 플랫폼 컴포넌트 설치 (AWS Load Balancer Controller, Argo CD)
#
# 사용법:
#   ./scripts/install-platform.sh <env> [component]
#
# 인자:
#   env       - 환경 (dev / prod)
#   component - 설치할 컴포넌트 (alb / argocd / all, 기본값: all)
#
# 예시:
#   ./scripts/install-platform.sh dev          # dev 환경 전체 설치
#   ./scripts/install-platform.sh dev alb      # dev 환경 ALB Controller만 설치
#   ./scripts/install-platform.sh prod argocd  # prod 환경 Argo CD만 설치
#
# 사전 요구사항:
#   - kubectl 설치 및 EKS 클러스터 접근 가능
#   - helm 3.x 설치
#   - AWS CLI 설치 및 인증 설정
#   - Terraform apply 완료 (VPC, EKS, IRSA 등)
# ============================================================================

set -euo pipefail

# ==== 색상 정의 ==============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==== 로깅 함수 ==============================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==== 인자 파싱 ==============================================================
if [ $# -lt 1 ]; then
    log_error "Usage: $0 <env> [component]"
    log_info "  env       - dev / prod"
    log_info "  component - alb / argocd / all (default: all)"
    exit 1
fi

ENV=$1
COMPONENT=${2:-all}

# ==== 환경 검증 ==============================================================
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    log_error "Invalid environment: $ENV (must be 'dev' or 'prod')"
    exit 1
fi

if [[ "$COMPONENT" != "alb" && "$COMPONENT" != "argocd" && "$COMPONENT" != "all" ]]; then
    log_error "Invalid component: $COMPONENT (must be 'alb', 'argocd', or 'all')"
    exit 1
fi

log_info "Environment: $ENV"
log_info "Component: $COMPONENT"

# ==== 디렉토리 설정 ==========================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HELM_DIR="$PROJECT_ROOT/infra/helm/platform"

log_info "Project root: $PROJECT_ROOT"

# ==== 사전 요구사항 확인 =====================================================
log_info "Checking prerequisites..."

# kubectl 확인
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl not found. Please install kubectl."
    exit 1
fi

# helm 확인
if ! command -v helm &> /dev/null; then
    log_error "helm not found. Please install helm 3.x."
    exit 1
fi

# AWS CLI 확인
if ! command -v aws &> /dev/null; then
    log_error "aws CLI not found. Please install AWS CLI."
    exit 1
fi

# kubectl 접근 확인
if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot access Kubernetes cluster. Please configure kubectl."
    log_info "Run: aws eks update-kubeconfig --name agent-t-$ENV-eks --region ap-northeast-2"
    exit 1
fi

log_success "Prerequisites check passed."

# ==== 클러스터 정보 가져오기 =================================================
log_info "Fetching cluster information..."

CLUSTER_NAME="agent-t-$ENV-eks"
REGION="ap-northeast-2"

# VPC ID 가져오기 (Terraform output 또는 AWS CLI)
VPC_ID=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig.vpcId' --output text 2>/dev/null || echo "")

if [ -z "$VPC_ID" ]; then
    log_warn "Could not fetch VPC ID automatically. Please set it manually in values file."
    VPC_ID="REPLACE_ME"
else
    log_success "VPC ID: $VPC_ID"
fi

# ==== Helm Repo 추가 =========================================================
log_info "Adding Helm repositories..."

helm repo add eks https://aws.github.io/eks-charts
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

log_success "Helm repositories added."

# ==== AWS Load Balancer Controller 설치 =====================================
install_alb_controller() {
    log_info "Installing AWS Load Balancer Controller..."

    local VALUES_FILE="$HELM_DIR/aws-load-balancer-controller/values-$ENV.yaml"

    if [ ! -f "$VALUES_FILE" ]; then
        log_error "Values file not found: $VALUES_FILE"
        exit 1
    fi

    # IRSA Role ARN 가져오기 (Terraform output 또는 수동 설정)
    local ROLE_ARN=""
    if command -v terraform &> /dev/null && [ -d "$PROJECT_ROOT/infra/terraform/envs/$ENV" ]; then
        cd "$PROJECT_ROOT/infra/terraform/envs/$ENV"
        ROLE_ARN=$(terraform output -raw alb_controller_role_arn 2>/dev/null || echo "")
        cd - > /dev/null
    fi

    if [ -z "$ROLE_ARN" ]; then
        log_warn "Could not fetch IRSA Role ARN automatically."
        log_warn "Please set serviceAccount.annotations.eks.amazonaws.com/role-arn in $VALUES_FILE"
        ROLE_ARN="REPLACE_ME"
    else
        log_success "IRSA Role ARN: $ROLE_ARN"

        # values 파일에 ROLE_ARN과 VPC_ID 자동 주입
        sed -i.bak "s|eks.amazonaws.com/role-arn: \".*\"|eks.amazonaws.com/role-arn: \"$ROLE_ARN\"|g" "$VALUES_FILE"
        sed -i.bak "s|vpcId: \".*\"|vpcId: \"$VPC_ID\"|g" "$VALUES_FILE"
        rm -f "${VALUES_FILE}.bak"
    fi

    # Helm install/upgrade
    helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
        --namespace kube-system \
        --values "$VALUES_FILE" \
        --wait \
        --timeout 5m

    log_success "AWS Load Balancer Controller installed."

    # 확인
    log_info "Verifying AWS Load Balancer Controller..."
    kubectl rollout status deployment aws-load-balancer-controller -n kube-system --timeout=2m

    # IngressClass 확인
    kubectl get ingressclass

    log_success "AWS Load Balancer Controller is ready."
}

# ==== Argo CD 설치 ===========================================================
install_argocd() {
    log_info "Installing Argo CD..."

    local VALUES_FILE="$HELM_DIR/argocd/values-$ENV.yaml"

    if [ ! -f "$VALUES_FILE" ]; then
        log_error "Values file not found: $VALUES_FILE"
        exit 1
    fi

    # argocd namespace 생성
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

    # Helm install/upgrade
    helm upgrade --install argocd argo/argo-cd \
        --namespace argocd \
        --values "$VALUES_FILE" \
        --wait \
        --timeout 10m

    log_success "Argo CD installed."

    # 확인
    log_info "Verifying Argo CD..."
    kubectl rollout status deployment argocd-server -n argocd --timeout=3m
    kubectl rollout status deployment argocd-repo-server -n argocd --timeout=3m
    kubectl rollout status statefulset argocd-application-controller -n argocd --timeout=3m

    log_success "Argo CD is ready."

    # Admin 초기 비밀번호 출력
    log_info "Fetching Argo CD admin password..."
    local ADMIN_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "")

    if [ -n "$ADMIN_PASSWORD" ]; then
        log_success "Argo CD admin password: $ADMIN_PASSWORD"
        log_info "Save this password securely. You can change it after first login."
    else
        log_warn "Could not fetch admin password. Check secret: argocd-initial-admin-secret"
    fi

    # Argo CD Server URL 출력
    if [ "$ENV" == "dev" ]; then
        log_info "Argo CD Server URL: http://argocd.dev.agent-t.local"
        log_info "Add to /etc/hosts: <ALB-DNS> argocd.dev.agent-t.local"
    else
        log_info "Argo CD Server URL: https://argocd.prod.agent-t.com"
    fi

    log_info "Access Argo CD:"
    log_info "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
    log_info "  Then visit: https://localhost:8080"
}

# ==== 설치 실행 ==============================================================
case "$COMPONENT" in
    alb)
        install_alb_controller
        ;;
    argocd)
        install_argocd
        ;;
    all)
        install_alb_controller
        echo ""
        install_argocd
        ;;
esac

# ==== 완료 메시지 ============================================================
echo ""
log_success "========================================="
log_success "Platform components installation completed!"
log_success "========================================="
echo ""

if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "alb" ]; then
    log_info "AWS Load Balancer Controller:"
    log_info "  kubectl get deployment aws-load-balancer-controller -n kube-system"
    log_info "  kubectl get ingressclass"
fi

if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "argocd" ]; then
    log_info "Argo CD:"
    log_info "  kubectl get pods -n argocd"
    log_info "  kubectl get ingress -n argocd"
fi

echo ""
log_info "Next steps:"
log_info "  1. Configure Argo CD repositories (infra/argocd/)"
log_info "  2. Create Argo CD Applications"
log_info "  3. Deploy services with Helm + Argo CD"
echo ""
