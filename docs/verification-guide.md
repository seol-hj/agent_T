# CI/CD 전체 흐름 검증 가이드

## 전체 흐름 요약

```
feature/cicd 브랜치 작업
  ↓ git push origin feature/cicd
GitHub PR 생성
  ↓ Merge to main
GitHub Actions 실행 (main 브랜치)
  ↓
Docker 빌드 → ECR push
  ↓
gitops/dev 업데이트
  ↓
Argo CD 감지 (3분 이내)
  ↓
Kubernetes 배포
```

---

## 1단계: GitHub Actions 확인

### 웹 UI로 확인
```
https://github.com/seol-hj/agent_T/actions
```

**확인 사항**:
- ✅ Workflow 실행됨 (초록 체크)
- ✅ "build-and-push" job 성공
- ✅ ECR에 이미지 push 성공
- ✅ "✅ Manifest updated and pushed to gitops/dev branch" 메시지

### CLI로 확인
```bash
# 최근 workflow 실행 목록
gh run list --limit 10

# 특정 workflow 로그 확인
gh run view <run-id> --log
```

---

## 2단계: gitops/dev 브랜치 확인

### 최신 커밋 확인
```bash
# gitops/dev 최신 상태 가져오기
git fetch origin gitops/dev

# 최근 커밋 확인
git log origin/gitops/dev --oneline -10

# 출력 예시:
# bf4f829 chore(helm): update analysis-service image to sha-a1b470b
# c8074b3 chore(helm): update simulation-service image to sha-a1b470b
# cf09548 chore(helm): update api-service image to sha-a1b470b
```

### 이미지 태그 확인
```bash
# api-service 이미지 태그 확인
git show origin/gitops/dev:infra/helm/services/api-service/values-dev.yaml | grep "tag:"

# 출력 예시:
#   tag: "sha-a1b470b"

# 모든 서비스 확인
for service in api-service frontend agent-service analysis-service report-service simulation-service; do
  echo -n "$service: "
  git show origin/gitops/dev:infra/helm/services/$service/values-dev.yaml 2>/dev/null | grep "tag:" | head -1 | awk '{print $2}'
done
```

**예상 결과**:
```
api-service: "sha-a1b470b"
frontend: "sha-a1b470b"
agent-service: "sha-a1b470b"
analysis-service: "sha-a1b470b"
report-service: "sha-a1b470b"
simulation-service: "sha-a1b470b"
```

---

## 3단계: Argo CD 확인

### Argo CD UI 접속
```bash
# Port forward
kubectl port-forward -n argocd svc/argocd-server 8080:80

# 브라우저 열기
# http://localhost:8080

# 로그인 (admin / 초기 비밀번호)
kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

### CLI로 Argo CD 확인
```bash
# 1. Argo CD Pod 상태
kubectl get pods -n argocd

# 출력 예시:
# NAME                                  READY   STATUS    RESTARTS
# argocd-server-xxx                     1/1     Running   0
# argocd-repo-server-xxx                1/1     Running   0
# argocd-application-controller-xxx     1/1     Running   0

# 2. Applications 목록
kubectl get applications -n argocd

# 출력 예시:
# NAME               SYNC STATUS   HEALTH STATUS
# api-service        Synced        Healthy
# frontend           Synced        Healthy
# agent-service      OutOfSync     Degraded  ← 문제 있음
```

### Application 상세 확인
```bash
# 특정 Application 상태
kubectl describe application api-service -n argocd

# 또는 YAML로 확인
kubectl get application api-service -n argocd -o yaml

# Sync 상태 확인
kubectl get application api-service -n argocd -o jsonpath='{.status.sync.status}'
# 출력: Synced (정상) / OutOfSync (업데이트 필요)

# Health 상태 확인
kubectl get application api-service -n argocd -o jsonpath='{.status.health.status}'
# 출력: Healthy (정상) / Degraded (문제)
```

---

## 4단계: 실제 Pod 확인

### Pod 목록 확인
```bash
# 모든 서비스 Pod 확인
kubectl get pods -A | grep -E "(api-service|frontend|agent-service|analysis-service|report-service|simulation-service)"

# 특정 네임스페이스 (default 또는 agent-t)
kubectl get pods -n default

# Pod 상세 정보
kubectl describe pod <pod-name> -n default
```

### 이미지 확인
```bash
# Pod가 사용 중인 이미지 확인
kubectl get pods -n default -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'

# 출력 예시:
# api-service-xxx    190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service:sha-a1b470b
# frontend-xxx       190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/frontend:sha-a1b470b
```

### Pod 로그 확인
```bash
# 최근 로그 확인
kubectl logs -n default -l app=api-service --tail=50

# 실시간 로그
kubectl logs -n default -l app=api-service -f
```

---

## 문제: "이미지를 못 가져와서 서비스가 안 됨"

### 원인 1: ECR 권한 문제

**확인**:
```bash
# Pod events 확인
kubectl describe pod <pod-name> -n default

# 출력에서 확인:
# Events:
#   Type     Reason          Message
#   Warning  Failed          Failed to pull image: ... unauthorized
```

**해결**:
```bash
# EKS Node가 ECR 접근 권한이 있는지 확인
aws iam get-role --role-name <eks-node-role>

# ECR 정책 확인
aws iam list-attached-role-policies --role-name <eks-node-role>

# AmazonEC2ContainerRegistryReadOnly 정책 필요
```

**수동 해결**:
```bash
# ECR 로그인 확인
aws ecr get-login-password --region ap-northeast-2

# ECR repository 존재 확인
aws ecr describe-repositories --region ap-northeast-2 | grep agent-t-dev

# 이미지 존재 확인
aws ecr describe-images --repository-name agent-t-dev/api-service --region ap-northeast-2
```

---

### 원인 2: Argo CD가 gitops/dev를 못 봄

**확인**:
```bash
# Application source 확인
kubectl get application api-service -n argocd -o yaml | grep -A 5 "source:"

# 출력:
#   source:
#     repoURL: https://github.com/seol-hj/agent_T.git
#     targetRevision: gitops/dev  # ← 올바른지 확인
#     path: infra/helm/services/api-service
```

**수정 필요 시**:
```bash
# Application 재적용
kubectl apply -f infra/argocd/applications/dev/api-service.yaml

# 또는 직접 수정
kubectl edit application api-service -n argocd
```

---

### 원인 3: 이미지 태그가 실제로 ECR에 없음

**확인**:
```bash
# gitops/dev의 이미지 태그
git show origin/gitops/dev:infra/helm/services/api-service/values-dev.yaml | grep "tag:"
# 출력: tag: "sha-a1b470b"

# ECR에 해당 태그 존재하는지 확인
aws ecr describe-images \
  --repository-name agent-t-dev/api-service \
  --region ap-northeast-2 \
  --query 'imageDetails[*].[imageTags[0], imagePushedAt]' \
  --output table

# sha-a1b470b가 있어야 함
```

**없으면**:
- GitHub Actions가 실패했거나
- ECR push가 안 됨
- GitHub Actions 로그 확인 필요

---

### 원인 4: Helm values 경로 오류

**확인**:
```bash
# Helm chart 구조 확인
ls -la infra/helm/services/api-service/

# 출력:
# Chart.yaml
# values-dev.yaml  ← 있어야 함
# templates/
```

**values-dev.yaml 내용 확인**:
```bash
cat infra/helm/services/api-service/values-dev.yaml

# 필수 필드 확인:
# image:
#   repository: 190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service
#   tag: "sha-xxx"
#   pullPolicy: IfNotPresent
```

---

## 수동 동기화 (강제 배포)

### Argo CD CLI
```bash
# Argo CD 로그인
argocd login localhost:8080 --username admin --password <password>

# Application 동기화
argocd app sync api-service

# 상태 확인
argocd app get api-service
```

### kubectl로 동기화
```bash
# Application에 sync annotation 추가
kubectl patch application api-service -n argocd \
  --type merge \
  -p '{"operation":{"sync":{"revision":"gitops/dev"}}}'

# 또는 syncPolicy 활성화 확인
kubectl get application api-service -n argocd -o yaml | grep -A 5 "syncPolicy:"
```

---

## 트러블슈팅 체크리스트

### ✅ GitHub Actions
- [ ] Workflow 실행 완료 (초록 체크)
- [ ] ECR push 성공 메시지
- [ ] gitops/dev push 성공 메시지

### ✅ gitops/dev 브랜치
- [ ] 최신 커밋에 서비스 이미지 업데이트 있음
- [ ] values-dev.yaml의 tag가 업데이트됨

### ✅ ECR
- [ ] Repository 존재 (`agent-t-dev/api-service`)
- [ ] 이미지 태그 존재 (`sha-xxx`)
- [ ] EKS Node가 ECR 접근 권한 있음

### ✅ Argo CD
- [ ] Argo CD Pod 실행 중
- [ ] Application이 생성됨
- [ ] `targetRevision: gitops/dev` 설정됨
- [ ] Sync Status = Synced
- [ ] Health Status = Healthy

### ✅ Kubernetes
- [ ] Pod가 Running 상태
- [ ] 이미지가 최신 태그
- [ ] 로그에 에러 없음

---

## 전체 검증 스크립트

```bash
#!/bin/bash

echo "=== CI/CD 전체 검증 ==="

# 1. gitops/dev 확인
echo -e "\n1️⃣ gitops/dev 최신 커밋:"
git fetch origin gitops/dev 2>&1 | grep -v "From"
git log origin/gitops/dev --oneline -5

# 2. 이미지 태그 확인
echo -e "\n2️⃣ 현재 이미지 태그:"
for service in api-service frontend agent-service; do
  echo -n "  $service: "
  git show origin/gitops/dev:infra/helm/services/$service/values-dev.yaml 2>/dev/null | grep "tag:" | head -1 | awk '{print $2}'
done

# 3. Argo CD Applications
echo -e "\n3️⃣ Argo CD Applications:"
kubectl get applications -n argocd 2>/dev/null || echo "  ⚠️ Argo CD 접근 불가 (kubeconfig 설정 확인)"

# 4. Pod 상태
echo -e "\n4️⃣ Pod 상태:"
kubectl get pods -n default 2>/dev/null | grep -E "(api-service|frontend|agent-service)" || echo "  ⚠️ Kubernetes 접근 불가"

# 5. ECR 이미지 확인 (최근 3개)
echo -e "\n5️⃣ ECR 이미지 (api-service 최근 3개):"
aws ecr describe-images \
  --repository-name agent-t-dev/api-service \
  --region ap-northeast-2 \
  --query 'sort_by(imageDetails,& imagePushedAt)[-3:].imageTags[0]' \
  --output table 2>/dev/null || echo "  ⚠️ ECR 접근 불가 (AWS credentials 설정 확인)"

echo -e "\n✅ 검증 완료"
```

---

## 빠른 문제 해결

### "Pod가 ImagePullBackOff 상태"
```bash
# 1. ECR에 이미지 있는지 확인
aws ecr describe-images --repository-name agent-t-dev/api-service --region ap-northeast-2

# 2. EKS Node IAM Role 확인
aws eks describe-nodegroup --cluster-name <cluster-name> --nodegroup-name <nodegroup-name>

# 3. 수동으로 이미지 pull 테스트
kubectl run test --image=190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service:sha-xxx --rm -it
```

### "Argo CD가 Synced 안 됨"
```bash
# 1. 수동 sync
argocd app sync api-service

# 2. Auto-sync 활성화 확인
kubectl get application api-service -n argocd -o jsonpath='{.spec.syncPolicy.automated}'
# 출력: {"prune":true,"selfHeal":true}

# 3. Repository 접근 확인
argocd repo list
```

### "GitHub Actions는 성공했는데 gitops/dev에 업데이트 없음"
```bash
# 1. GitHub Actions 로그에서 "Commit manifest changes" 단계 확인
# 2. "No changes to commit" 메시지 확인
# 3. 실제로 values-dev.yaml이 변경되었는지 확인

git diff origin/main:infra/helm/services/api-service/values-dev.yaml origin/gitops/dev:infra/helm/services/api-service/values-dev.yaml
```

---

**작성일**: 2026-05-11  
**관련 문서**: 
- [branch-strategy-final.md](./branch-strategy-final.md)
- [ci-fixes-2026-05-11-final.md](./ci-fixes-2026-05-11-final.md)
