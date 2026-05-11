#!/bin/bash

# Argo CD 문제 진단 스크립트

echo "======================================"
echo "  Argo CD 문제 진단"
echo "======================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Argo CD Pod 상태
echo -e "\n${YELLOW}[1/7] Argo CD Pod 상태${NC}"
if kubectl get pods -n argocd &> /dev/null; then
  kubectl get pods -n argocd

  # Pod가 Running인지 확인
  NOT_RUNNING=$(kubectl get pods -n argocd --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
  if [ "$NOT_RUNNING" -gt 0 ]; then
    echo -e "${RED}⚠️  $NOT_RUNNING 개의 Pod가 Running 상태가 아닙니다${NC}"
  else
    echo -e "${GREEN}✅ 모든 Argo CD Pod가 Running 상태입니다${NC}"
  fi
else
  echo -e "${RED}❌ Argo CD 네임스페이스 접근 불가 (kubeconfig 설정 확인)${NC}"
  exit 1
fi

# 2. Argo CD Applications
echo -e "\n${YELLOW}[2/7] Argo CD Applications${NC}"
kubectl get applications -n argocd 2>/dev/null

APP_COUNT=$(kubectl get applications -n argocd --no-headers 2>/dev/null | wc -l)
if [ "$APP_COUNT" -eq 0 ]; then
  echo -e "${RED}❌ Application이 하나도 없습니다${NC}"
  echo -e "${YELLOW}💡 Application 생성:${NC}"
  echo "   kubectl apply -f infra/argocd/applications/dev/"
else
  echo -e "${GREEN}✅ $APP_COUNT 개의 Application 발견${NC}"
fi

# 3. Application 상세 (api-service 예시)
echo -e "\n${YELLOW}[3/7] api-service Application 상세${NC}"
if kubectl get application api-service -n argocd &> /dev/null; then
  echo "Repository URL:"
  kubectl get application api-service -n argocd -o jsonpath='{.spec.source.repoURL}' 2>/dev/null
  echo

  echo "Target Revision:"
  kubectl get application api-service -n argocd -o jsonpath='{.spec.source.targetRevision}' 2>/dev/null
  echo

  echo "Sync Status:"
  SYNC_STATUS=$(kubectl get application api-service -n argocd -o jsonpath='{.status.sync.status}' 2>/dev/null)
  echo "  $SYNC_STATUS"

  if [ "$SYNC_STATUS" != "Synced" ]; then
    echo -e "${RED}⚠️  OutOfSync 상태입니다${NC}"
    echo -e "${YELLOW}💡 수동 동기화:${NC}"
    echo "   kubectl patch application api-service -n argocd --type merge -p '{\"operation\":{\"sync\":{\"revision\":\"gitops/dev\"}}}'"
  else
    echo -e "${GREEN}✅ Sync 상태 정상${NC}"
  fi

  echo "Health Status:"
  HEALTH_STATUS=$(kubectl get application api-service -n argocd -o jsonpath='{.status.health.status}' 2>/dev/null)
  echo "  $HEALTH_STATUS"

  if [ "$HEALTH_STATUS" != "Healthy" ]; then
    echo -e "${RED}⚠️  Healthy 상태가 아닙니다${NC}"
  else
    echo -e "${GREEN}✅ Health 상태 정상${NC}"
  fi
else
  echo -e "${RED}❌ api-service Application이 없습니다${NC}"
  echo -e "${YELLOW}💡 Application 생성:${NC}"
  echo "   kubectl apply -f infra/argocd/applications/dev/api-service.yaml"
fi

# 4. 실제 Pod 상태
echo -e "\n${YELLOW}[4/7] 서비스 Pod 상태${NC}"
PODS=$(kubectl get pods -A 2>/dev/null | grep -E "(api-service|frontend|agent-service|analysis-service|report-service|simulation-service)")

if [ -z "$PODS" ]; then
  echo -e "${RED}❌ 서비스 Pod가 하나도 없습니다${NC}"
  echo -e "${YELLOW}💡 Argo CD가 아직 배포하지 않았거나 배포 실패${NC}"
else
  echo "$PODS"

  # ImagePullBackOff 확인
  IMAGE_PULL_ERROR=$(echo "$PODS" | grep -i "ImagePullBackOff\|ErrImagePull" | wc -l)
  if [ "$IMAGE_PULL_ERROR" -gt 0 ]; then
    echo -e "${RED}⚠️  $IMAGE_PULL_ERROR 개의 Pod가 이미지 Pull 실패${NC}"
  fi
fi

# 5. ECR 이미지 확인
echo -e "\n${YELLOW}[5/7] ECR 이미지 확인 (api-service 최근 5개)${NC}"
if aws ecr describe-images \
  --repository-name agent-t-dev/api-service \
  --region ap-northeast-2 \
  --query 'sort_by(imageDetails,& imagePushedAt)[-5:].{Tag:imageTags[0], Pushed:imagePushedAt}' \
  --output table 2>/dev/null; then
  echo -e "${GREEN}✅ ECR 접근 성공${NC}"
else
  echo -e "${RED}❌ ECR 접근 실패 (AWS credentials 확인)${NC}"
fi

# 6. gitops/dev 브랜치 확인
echo -e "\n${YELLOW}[6/7] gitops/dev 브랜치 이미지 태그${NC}"
git fetch origin gitops/dev 2>&1 | grep -v "From"

for service in api-service frontend agent-service analysis-service report-service simulation-service; do
  TAG=$(git show origin/gitops/dev:infra/helm/services/$service/values-dev.yaml 2>/dev/null | grep "tag:" | head -1 | awk '{print $2}' | tr -d '"')
  if [ -n "$TAG" ]; then
    echo "  $service: $TAG"
  else
    echo -e "  $service: ${RED}태그 없음${NC}"
  fi
done

# 7. 특정 Pod의 이미지 Pull 오류 확인 (있다면)
echo -e "\n${YELLOW}[7/7] Pod 이벤트 확인 (문제 있는 경우만)${NC}"
PROBLEM_PODS=$(kubectl get pods -A 2>/dev/null | grep -E "ImagePullBackOff|ErrImagePull|CrashLoopBackOff" | awk '{print $1":"$2}')

if [ -n "$PROBLEM_PODS" ]; then
  echo "$PROBLEM_PODS" | while IFS=: read namespace pod; do
    echo -e "\n${RED}Pod: $namespace/$pod${NC}"
    kubectl describe pod "$pod" -n "$namespace" 2>/dev/null | grep -A 10 "Events:" | tail -10
  done
else
  echo -e "${GREEN}✅ 문제가 있는 Pod가 없습니다${NC}"
fi

# 요약
echo -e "\n======================================"
echo -e "  ${YELLOW}진단 완료${NC}"
echo "======================================"

echo -e "\n${YELLOW}다음 단계:${NC}"
echo "1. Argo CD UI 확인: kubectl port-forward -n argocd svc/argocd-server 8080:80"
echo "   http://localhost:8080"
echo ""
echo "2. 수동 동기화 (필요 시):"
echo "   kubectl patch application api-service -n argocd --type merge -p '{\"operation\":{\"sync\":{\"revision\":\"gitops/dev\"}}}'"
echo ""
echo "3. Application 재생성 (없는 경우):"
echo "   kubectl apply -f infra/argocd/applications/dev/"
echo ""
echo "4. Pod 로그 확인 (문제 있는 경우):"
echo "   kubectl logs -n default <pod-name>"
