#!/usr/bin/env bash
# ============================================================================
# generate-argocd-apps.sh
# 책임: 나머지 서비스들의 Argo CD Application 생성
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APPS_DIR="$PROJECT_ROOT/infra/argocd/applications/dev"

SERVICES=(
  "agent-service"
  "simulation-service"
  "analysis-service"
  "report-service"
  "frontend"
)

TEMPLATE_SERVICE="api-service"

for SERVICE in "${SERVICES[@]}"; do
  echo "Generating Argo CD Application for $SERVICE..."

  sed "s/api-service/$SERVICE/g" \
    "$APPS_DIR/$TEMPLATE_SERVICE.yaml" > "$APPS_DIR/$SERVICE.yaml"

  echo "✓ $SERVICE application generated"
done

echo ""
echo "All Argo CD Applications generated successfully!"
echo "Location: $APPS_DIR"
