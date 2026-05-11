#!/bin/bash

echo "======================================"
echo "  Argo CD 즉시 동기화"
echo "======================================"

echo -e "\n모든 Application을 gitops/dev에서 동기화합니다...\n"

for app in frontend api-service agent-service analysis-service report-service simulation-service; do
  echo "🔄 Syncing $app..."
  kubectl patch application $app -n argocd \
    --type merge \
    -p '{"operation":{"sync":{"revision":"gitops/dev"}}}' 2>/dev/null

  if [ $? -eq 0 ]; then
    echo "✅ $app sync initiated"
  else
    echo "⚠️  $app not found or already syncing"
  fi
  echo ""
done

echo "======================================"
echo "✅ 동기화 요청 완료"
echo "======================================"

echo -e "\n다음 명령어로 상태 확인:"
echo "  watch kubectl get pods -n default"
echo ""
echo "Pod 로그 확인 (예시):"
echo "  kubectl logs -n default -l app=agent-service --tail=50"
echo ""
echo "Argo CD UI:"
echo "  kubectl port-forward -n argocd svc/argocd-server 8080:80"
echo "  http://localhost:8080"
