# GitOps 브랜치 전략 최종 적용 - 2026-05-11

## 변경 요약

main 브랜치 protection을 우회하기 위해 **GitOps 표준 방식**을 적용했습니다.

---

## 적용된 변경사항

### 1. GitHub Actions 워크플로우 (7개)

#### 모든 CI 워크플로우 (6개)
- **파일**: 
  - `.github/workflows/ci-frontend.yml`
  - `.github/workflows/ci-agent-service.yml`
  - `.github/workflows/ci-analysis-service.yml`
  - `.github/workflows/ci-api-service.yml`
  - `.github/workflows/ci-report-service.yml`
  - `.github/workflows/ci-simulation-service.yml`

**변경 1: 트리거 브랜치**
```yaml
# Before
on:
  push:
    branches: [main, develop]  # ❌
  pull_request:
    branches: [main, develop]  # ❌

# After
on:
  push:
    branches: [main]  # ✅
  pull_request:
    branches: [main]  # ✅
```

**변경 2: Permissions 추가**
```yaml
# 추가
name: CI - XXX Service

permissions:
  contents: write  # Git push 권한 (build-and-push.yml 호출 시 필요)

on:
  push:
```

---

#### build-and-push.yml
- **파일**: `.github/workflows/build-and-push.yml`

**변경: GitOps 브랜치로 Push**
```yaml
# Before
- name: Commit manifest changes
  run: |
    git commit -m "..."
    git push  # ❌ main 브랜치에 push → 권한 오류

# After
- name: Commit manifest changes to GitOps branch
  run: |
    # gitops/dev 브랜치로 checkout (없으면 생성)
    git fetch origin gitops/dev || true
    git checkout -B gitops/dev origin/gitops/dev || git checkout -B gitops/dev
    
    git add "$HELM_VALUES_PATH"
    git commit -m "chore(helm): update ... image to ..."
    git push origin gitops/dev  # ✅ gitops/dev에 push
```

---

### 2. Argo CD 설정 (8개)

#### Applications (7개)
- **파일**:
  - `infra/argocd/applications/dev/frontend.yaml`
  - `infra/argocd/applications/dev/agent-service.yaml`
  - `infra/argocd/applications/dev/analysis-service.yaml`
  - `infra/argocd/applications/dev/api-service.yaml`
  - `infra/argocd/applications/dev/report-service.yaml`
  - `infra/argocd/applications/dev/simulation-service.yaml`
  - `infra/argocd/applications/dev/gateway.yaml`

**변경 1: Repository URL**
```yaml
# Before
repoURL: https://github.com/YOUR_ORG/agent-t.git  # ❌

# After
repoURL: https://github.com/seol-hj/agent_T.git  # ✅
```

**변경 2: Target Revision**
```yaml
# Before
targetRevision: develop  # ❌

# After
targetRevision: gitops/dev  # ✅
```

---

#### ApplicationSet
- **파일**: `infra/argocd/applicationsets/services-dev.yaml`

**동일한 변경**:
- Repository URL 수정
- `targetRevision: gitops/dev`

---

### 3. 문서 추가

#### branch-strategy-final.md
- **파일**: `docs/branch-strategy-final.md`
- **내용**: 
  - 브랜치 전략 상세 설명
  - 개발자 워크플로우 (Step by Step)
  - 트러블슈팅 가이드

#### gitops-branch-setup.md
- **파일**: `docs/gitops-branch-setup.md`
- **내용**: 
  - GitOps 브랜치 초기 설정
  - 작동 방식 설명
  - 검증 방법

---

## 브랜치 전략

### 브랜치별 역할

| 브랜치 | 용도 | 누가 작업 | 보호 |
|--------|------|-----------|------|
| **feature/\*** | 개발 작업 | 개발자 직접 | 없음 |
| **main** | 소스 코드 | PR merge만 | ✅ Protection |
| **gitops/dev** | 배포 명세 | GitHub Actions만 | ❌ Protection 금지 |

---

### 전체 워크플로우

```
┌────────────────────────────────────────────────────────────┐
│ 1. 개발자 작업 (feature/add-api 브랜치)                      │
│    - git checkout -b feature/add-api                      │
│    - 코드 수정                                             │
│    - git push origin feature/add-api                      │
└────────────────┬───────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────┐
│ 2. GitHub PR 생성 (feature/add-api → main)                 │
│    - Web UI에서 "Create pull request"                     │
│    - 리뷰 및 승인                                          │
└────────────────┬───────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────┐
│ 3. PR Merge                                                │
│    - "Merge pull request" 버튼 클릭                        │
│    - ⭐ main 브랜치에 push 이벤트 발생!                     │
└────────────────┬───────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────┐
│ 4. GitHub Actions 자동 실행                                 │
│    - Docker 이미지 빌드                                     │
│    - ECR에 push (agent-t-dev/xxx:sha-abc1234)             │
│    - values-dev.yaml 업데이트                              │
│    - gitops/dev 브랜치에 commit & push                     │
└────────────────┬───────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────┐
│ 5. Argo CD 자동 배포 (3분 이내)                             │
│    - gitops/dev 브랜치 변경 감지                            │
│    - Helm chart 동기화                                     │
│    - Kubernetes에 새 이미지 배포                            │
└────────────────────────────────────────────────────────────┘
```

---

## 왜 이렇게 했는가?

### 문제: main 브랜치 Protection

```
GitHub Actions가 main에 values 업데이트 push 시도
  ↓
❌ "Permission denied" (Branch protection)
  ↓
💥 CI/CD 실패
```

---

### 해결: GitOps 브랜치 분리

```
소스 코드 (main) ≠ 배포 명세 (gitops/dev)
```

**장점**:
1. ✅ main 브랜치 protection 유지 가능
2. ✅ GitHub Actions가 자유롭게 gitops/dev에 push
3. ✅ 배포 히스토리 명확 (gitops/dev 커밋 로그)
4. ✅ 롤백 간편 (git revert on gitops/dev)
5. ✅ GitOps 표준 패턴

---

## 초기 설정 (1회만)

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

---

### 2. Repository Settings 확인

```
Settings → Actions → General → Workflow permissions
✅ Read and write permissions
```

---

### 3. Branch Protection 확인

**main 브랜치**:
```
Settings → Branches → Branch protection rules → main
✅ Require pull request reviews
✅ Require status checks to pass
```

**gitops/dev 브랜치**:
```
⚠️ Branch protection 설정하지 말 것!
(GitHub Actions가 자동으로 push해야 함)
```

---

## 테스트 방법

### 1. Feature 브랜치 생성 및 작업
```bash
git checkout main
git pull origin main
git checkout -b feature/test-gitops

# 코드 수정
echo "test" >> apps/api-service/README.md

git add apps/api-service/
git commit -m "test: verify gitops workflow"
git push origin feature/test-gitops
```

---

### 2. PR 생성 및 Merge
```
1. GitHub Web UI 접속
2. "Compare & pull request" 클릭
3. Base: main ← Compare: feature/test-gitops
4. "Create pull request"
5. (리뷰 후) "Merge pull request" 클릭
```

---

### 3. GitHub Actions 확인
```
https://github.com/seol-hj/agent_T/actions

✅ "CI - API Service" workflow 실행 중
✅ build-and-push job 성공
✅ "Manifest updated and pushed to gitops/dev branch" 메시지
```

---

### 4. gitops/dev 브랜치 확인
```bash
git fetch origin gitops/dev
git log origin/gitops/dev --oneline -5

# 출력 예시:
# abc1234 chore(helm): update api-service image to sha-xyz7890
# def5678 chore(helm): update frontend image to sha-abc1234
```

---

### 5. Argo CD 배포 확인
```bash
# Argo CD UI 확인
kubectl port-forward -n argocd svc/argocd-server 8080:80
# http://localhost:8080

# 또는 CLI
argocd app get api-service

# Pod 확인
kubectl get pods -l app=api-service
kubectl describe pod -l app=api-service | grep Image:
# agent-t-dev/api-service:sha-xyz7890
```

---

## 검증 체크리스트

### ✅ GitHub Actions
- [ ] 6개 CI 워크플로우가 `branches: [main]`만 트리거
- [ ] 모든 CI 워크플로우에 `permissions: contents: write` 추가
- [ ] build-and-push.yml이 `gitops/dev`에 push

### ✅ Argo CD
- [ ] 7개 Application이 `targetRevision: gitops/dev`
- [ ] ApplicationSet도 `targetRevision: gitops/dev`
- [ ] Repository URL이 `seol-hj/agent_T`

### ✅ 브랜치
- [ ] gitops/dev 브랜치 생성됨
- [ ] gitops/dev에 branch protection 없음
- [ ] main에 branch protection 유지

---

## 트러블슈팅

### 문제: "gitops/dev 브랜치가 없습니다"
```bash
git checkout main
git checkout -b gitops/dev
git push origin gitops/dev
```

---

### 문제: "Permission denied to gitops/dev"
**원인**: Branch protection 설정됨

**해결**:
```
Settings → Branches → Branch protection rules
→ gitops/dev rule 삭제
```

---

### 문제: "Argo CD가 배포 안 함"
**확인 1**: targetRevision
```bash
kubectl get application -n argocd api-service -o yaml | grep targetRevision
# 출력: targetRevision: gitops/dev
```

**확인 2**: gitops/dev 커밋 있는지
```bash
git log origin/gitops/dev --oneline -5
```

**수동 동기화**:
```bash
argocd app sync api-service
```

---

## 파일 변경 목록

### GitHub Actions (7개)
```
.github/workflows/ci-frontend.yml
.github/workflows/ci-agent-service.yml
.github/workflows/ci-analysis-service.yml
.github/workflows/ci-api-service.yml
.github/workflows/ci-report-service.yml
.github/workflows/ci-simulation-service.yml
.github/workflows/build-and-push.yml
```

### Argo CD (8개)
```
infra/argocd/applications/dev/frontend.yaml
infra/argocd/applications/dev/agent-service.yaml
infra/argocd/applications/dev/analysis-service.yaml
infra/argocd/applications/dev/api-service.yaml
infra/argocd/applications/dev/report-service.yaml
infra/argocd/applications/dev/simulation-service.yaml
infra/argocd/applications/dev/gateway.yaml
infra/argocd/applicationsets/services-dev.yaml
```

### 문서 (3개)
```
docs/branch-strategy-final.md (신규)
docs/gitops-branch-setup.md (신규)
docs/CHANGES-2026-05-11-gitops.md (이 파일)
```

---

## 다음 단계

### 1. gitops/dev 브랜치 생성 (최초 1회)
```bash
git checkout main
git pull origin main
git checkout -b gitops/dev
git push origin gitops/dev
git checkout main
```

### 2. 변경사항 커밋
```bash
git add .github/workflows/
git add infra/argocd/
git add docs/
git commit -m "feat: implement GitOps branch strategy

- GitHub Actions pushes to gitops/dev (bypasses main protection)
- Argo CD watches gitops/dev for automated deployment
- main branch remains protected for source code only
- Separate concerns: source code (main) vs deployment manifests (gitops/dev)"

git push origin main
```

### 3. Argo CD Applications 재적용
```bash
kubectl apply -f infra/argocd/applications/dev/
kubectl apply -f infra/argocd/applicationsets/services-dev.yaml
```

---

**작성일**: 2026-05-11  
**상태**: 완료 ✅  
**적용 범위**: 
- GitHub Actions: 7개 workflow 수정
- Argo CD: 8개 Application 수정
- 문서: 3개 신규 작성

**관련 문서**: 
- [branch-strategy-final.md](./branch-strategy-final.md)
- [gitops-branch-setup.md](./gitops-branch-setup.md)
- [ci-fixes-final-2026-05-11.md](./ci-fixes-final-2026-05-11.md)
