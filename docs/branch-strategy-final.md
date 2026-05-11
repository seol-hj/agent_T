# 브랜치 전략 최종 확정 - 2026-05-11

## 브랜치 구조

### 1. main 브랜치 (소스 코드)
- **용도**: 프로덕션 소스 코드
- **보호**: Branch protection rule 활성화 (직접 push 불가)
- **업데이트**: PR merge를 통해서만 가능
- **GitHub Actions**: main에 push 이벤트 발생 시 자동 실행

### 2. feature/* 브랜치 (개발 작업)
- **용도**: 개발자 작업 브랜치
- **명명**: `feature/add-user-api`, `feature/fix-login-bug` 등
- **작업 흐름**: 자유롭게 commit & push
- **목적지**: main 브랜치로 PR

### 3. gitops/dev 브랜치 (배포 명세 - 자동화 전용)
- **용도**: Helm values 배포 명세 (image tag만)
- **업데이트**: GitHub Actions만 자동 push ⚠️
- **사람**: 직접 작업 절대 금지 ❌
- **Argo CD**: 이 브랜치를 감시하여 자동 배포

---

## 워크플로우 (전체 흐름)

```
┌─────────────────┐
│  개발자 로컬     │
│  feature/xxx    │
└────────┬────────┘
         │ git push origin feature/xxx
         ↓
┌─────────────────┐
│  GitHub         │
│  feature → main │ ← PR 생성, 리뷰, 승인
│  (PR)           │
└────────┬────────┘
         │ Merge PR (Merge 버튼 클릭)
         ↓
┌─────────────────┐
│  main 브랜치    │ ← ⭐ push 이벤트 발생
│  (protected)    │
└────────┬────────┘
         │ GitHub Actions 트리거
         ↓
┌─────────────────┐
│  GitHub Actions │
│  1. 빌드        │
│  2. ECR push    │
│  3. values 업데이트 │
└────────┬────────┘
         │ git push origin gitops/dev
         ↓
┌─────────────────┐
│  gitops/dev     │ ← Helm values 자동 업데이트
│  (자동화 전용)   │
└────────┬────────┘
         │ Argo CD 폴링 (3분마다)
         ↓
┌─────────────────┐
│  Argo CD        │
│  자동 배포      │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Kubernetes     │
│  EKS Cluster    │
└─────────────────┘
```

---

## 개발자 작업 예시

### Step 1: Feature 브랜치 생성
```bash
git checkout main
git pull origin main
git checkout -b feature/add-search-api
```

### Step 2: 코드 작성
```bash
# apps/api-service/main.py 수정
vim apps/api-service/main.py

# 로컬 테스트
docker compose up api-service

# Commit
git add apps/api-service/
git commit -m "feat: add search API endpoint"
```

### Step 3: Push (Feature 브랜치)
```bash
git push origin feature/add-search-api
# ⭐ 이 push는 main이 아니므로 GitHub Actions 실행 안 됨
```

### Step 4: PR 생성 (GitHub Web UI)
```
1. https://github.com/seol-hj/agent_T 접속
2. "Compare & pull request" 클릭
3. Base: main ← Compare: feature/add-search-api
4. PR 제목, 설명 작성
5. "Create pull request" 클릭
```

**이때 자동으로**:
- `build-validation` job 실행 (Docker 빌드만, ECR push 안 함)
- 코드 검증용

### Step 5: PR 리뷰 및 승인
```
1. 팀원 코드 리뷰
2. "Approve" 클릭
3. CI 검증 통과 확인
```

### Step 6: Merge PR
```
GitHub Web UI에서 "Merge pull request" 클릭
↓
"Confirm merge" 클릭
↓
⭐⭐⭐ main 브랜치에 push 이벤트 발생! ⭐⭐⭐
```

### Step 7: GitHub Actions 자동 실행 (아무것도 안 해도 됨!)
```
[자동] determine-env job 실행
  → ECR repository 결정 (agent-t-dev/api-service)

[자동] build-and-push job 실행
  → Docker 이미지 빌드
  → ECR push (190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service:sha-abc1234)
  → infra/helm/services/api-service/values-dev.yaml 업데이트
  → gitops/dev 브랜치에 commit & push
```

### Step 8: Argo CD 자동 배포 (3분 이내)
```
[자동] Argo CD가 gitops/dev 브랜치 감지
[자동] Helm chart 동기화
[자동] Kubernetes에 새 이미지 배포
[자동] Pod 재시작 (Rolling update)
```

### Step 9: 배포 확인
```bash
# Pod 확인
kubectl get pods -l app=api-service

# 새 이미지 확인
kubectl describe pod -l app=api-service | grep Image:
# 출력: agent-t-dev/api-service:sha-abc1234

# 로그 확인
kubectl logs -l app=api-service --tail=50
```

---

## GitHub Actions 트리거 설정 (최종)

### 모든 CI 워크플로우 (6개)

```yaml
# .github/workflows/ci-*.yml

on:
  push:
    branches: [main]  # ✅ main만!
    paths:
      - "apps/xxx/**"
  pull_request:
    branches: [main]  # ✅ main만!
    paths:
      - "apps/xxx/**"
```

**설정된 워크플로우**:
- ✅ `ci-frontend.yml`
- ✅ `ci-agent-service.yml`
- ✅ `ci-analysis-service.yml`
- ✅ `ci-api-service.yml`
- ✅ `ci-report-service.yml`
- ✅ `ci-simulation-service.yml`

**제거된 브랜치**:
- ❌ `develop` (사용 안 함)
- ❌ `gitops/dev`에서 트리거 안 함 (Actions만 push)

---

## Argo CD 설정 (최종)

### Application 설정

```yaml
# infra/argocd/applications/dev/*.yaml

spec:
  source:
    repoURL: https://github.com/seol-hj/agent_T.git
    targetRevision: gitops/dev  # ✅ gitops/dev 감시
    path: infra/helm/services/api-service
    helm:
      valueFiles:
        - values-dev.yaml
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**설정된 Application**:
- ✅ `frontend`
- ✅ `agent-service`
- ✅ `analysis-service`
- ✅ `api-service`
- ✅ `report-service`
- ✅ `simulation-service`
- ✅ `gateway`

---

## 브랜치 보호 설정

### main 브랜치 (Repository Settings)

```
Settings → Branches → Branch protection rules → main

필수 설정:
✅ Require a pull request before merging
  ✅ Require approvals (최소 1명)
✅ Require status checks to pass before merging
  ✅ build-validation
✅ Require conversation resolution before merging
```

### gitops/dev 브랜치

```
⚠️ Branch protection 설정하지 말 것!
- GitHub Actions가 자동으로 push해야 함
- 보호 설정 시 Actions 실패
```

---

## 환경별 전략 (향후 확장)

### Development (현재)
```
작업 브랜치: feature/*
코드 브랜치: main
배포 브랜치: gitops/dev
ECR: agent-t-dev/*
Argo CD: targetRevision: gitops/dev
```

### Production (향후)
```
작업 브랜치: release/*
코드 브랜치: release/v1.x
배포 브랜치: gitops/prod
ECR: agent-t-prod/*
Argo CD: targetRevision: gitops/prod
```

---

## 초기 설정 (한 번만)

### 1. gitops/dev 브랜치 생성

```bash
cd /mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t

git checkout main
git pull origin main

# gitops/dev 브랜치 생성
git checkout -b gitops/dev
git push origin gitops/dev

# main으로 돌아가기
git checkout main
```

### 2. Repository Settings 확인

```
Settings → Actions → General → Workflow permissions
✅ Read and write permissions
```

### 3. Branch Protection 설정

```
Settings → Branches → Add branch protection rule

Branch name pattern: main
✅ Require pull request reviews before merging
✅ Require status checks to pass
```

---

## 트러블슈팅

### 문제: "main 브랜치에 직접 push 불가"
**예상 동작**: Branch protection이 정상 작동 중
**해결**: Feature 브랜치 → PR → Merge

---

### 문제: "PR merge 후 Actions 실행 안 됨"
**확인 1**: Workflow 트리거 브랜치
```bash
grep "branches:" .github/workflows/ci-api-service.yml
# 출력: branches: [main]  ← 정상
```

**확인 2**: 파일 경로 매칭
```yaml
# apps/api-service/ 아래 파일만 트리거
paths:
  - "apps/api-service/**"
```

다른 서비스 파일 수정했으면 트리거 안 됨 (정상)

---

### 문제: "gitops/dev에 push 실패"
**원인**: Branch protection 설정됨
**해결**: gitops/dev의 protection rule 제거

```
Settings → Branches → Branch protection rules
→ gitops/dev 삭제
```

---

### 문제: "Argo CD가 배포 안 함"
**확인 1**: targetRevision
```bash
kubectl get application -n argocd api-service -o yaml | grep targetRevision
# 출력: targetRevision: gitops/dev
```

**확인 2**: gitops/dev 브랜치에 commit 있는지
```bash
git log origin/gitops/dev --oneline -5
```

**확인 3**: Argo CD 수동 동기화
```bash
argocd app sync api-service
```

---

## 핵심 요약

### ✅ 정상 동작
1. Feature 브랜치에서 작업
2. main으로 PR
3. PR merge → main에 push 이벤트 발생
4. GitHub Actions 자동 실행
5. gitops/dev 자동 업데이트
6. Argo CD 자동 배포

### ❌ 하지 말아야 할 것
1. main 브랜치에 직접 push (불가능 + 하지 말 것)
2. gitops/dev 브랜치에서 직접 작업 (Actions 전용)
3. gitops/dev에 branch protection 설정 (Actions 실패)

### 🔑 브랜치별 역할
- **feature/***: 개발자가 작업 (자유)
- **main**: 소스 코드 (PR만, protected)
- **gitops/dev**: 배포 명세 (Actions 전용, 사람 접근 금지)

---

**작성일**: 2026-05-11  
**상태**: 최종 확정 ✅  
**검증**: 
- ✅ 모든 CI 워크플로우 main 브랜치만 트리거
- ✅ 모든 Argo CD Application이 gitops/dev 감시
- ✅ GitHub Actions가 gitops/dev에 자동 push

**관련 문서**: 
- [gitops-branch-setup.md](./gitops-branch-setup.md)
- [ci-fixes-final-2026-05-11.md](./ci-fixes-final-2026-05-11.md)
