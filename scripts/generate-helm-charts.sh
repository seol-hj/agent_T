#!/usr/bin/env bash
# ============================================================================
# generate-helm-charts.sh
# 책임: 나머지 서비스들의 Helm Chart 생성 (api-service를 템플릿으로 사용)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICES_DIR="$PROJECT_ROOT/infra/helm/services"

SERVICES=(
  "agent-service"
  "simulation-service"
  "analysis-service"
  "report-service"
  "frontend"
)

# api-service를 템플릿으로 사용
TEMPLATE_SERVICE="api-service"

for SERVICE in "${SERVICES[@]}"; do
  echo "Generating Helm chart for $SERVICE..."

  SERVICE_DIR="$SERVICES_DIR/$SERVICE"
  mkdir -p "$SERVICE_DIR/templates"

  # Chart.yaml 복사 및 수정
  sed "s/api-service/$SERVICE/g; s/API Service/${SERVICE^} Service/g" \
    "$SERVICES_DIR/$TEMPLATE_SERVICE/Chart.yaml" > "$SERVICE_DIR/Chart.yaml"

  # values.yaml 복사 및 수정
  sed "s/api-service/$SERVICE/g" \
    "$SERVICES_DIR/$TEMPLATE_SERVICE/values.yaml" > "$SERVICE_DIR/values.yaml"

  # values-dev.yaml 복사 및 수정
  sed "s/api-service/$SERVICE/g" \
    "$SERVICES_DIR/$TEMPLATE_SERVICE/values-dev.yaml" > "$SERVICE_DIR/values-dev.yaml"

  # templates 복사 및 수정
  for TEMPLATE_FILE in "$SERVICES_DIR/$TEMPLATE_SERVICE/templates"/*.yaml "$SERVICES_DIR/$TEMPLATE_SERVICE/templates"/*.tpl; do
    FILENAME=$(basename "$TEMPLATE_FILE")
    sed "s/api-service/$SERVICE/g" "$TEMPLATE_FILE" > "$SERVICE_DIR/templates/$FILENAME"
  done

  echo "✓ $SERVICE chart generated"
done

echo ""
echo "All service charts generated successfully!"
echo "Location: $SERVICES_DIR"
