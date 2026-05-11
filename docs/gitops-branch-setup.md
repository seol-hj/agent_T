# GitOps Branch 설정 가이드

## 개요

이 프로젝트는 **GitOps 표준 방식**을 사용합니다:

- **main 브랜치**: 소스 코드 (branch protection 적용)
- **gitops/dev 브랜치**: Helm values 자동 업데이트 (GitHub Actions가 push)

```
소스 코드 변경 (main)
  → GitHub Actions 빌드
  → ECR 이미지 푸시
  → Helm values 업데이트 (gitops/dev)
  → Argo CD 자동 배포
```

---

## 초기 설정

### 1. gitops/dev 브랜치 생성

```bash
cd /mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t

# main 브랜치에서 gitops/dev 생성
git checkout main
git pull origin main

# gitops/dev 브랜치 생성 및 push
git checkout -b gitops/dev
git push origin gitops/dev

# main으로 돌아가기
git checkout main
```

---

### 2. Branch Protection 설정 (선택)

**gitops/dev 브랜치는 protection 불필요**:
- GitHub Actions만 push
- 사람이 직접 commit 안 함
- Force push 허용 (값 업데이트만)

**main 브랜치는 protection 유지**:
```
Repository → Settings → Branches → Branch protection rules

main:
✅ Require pull request reviews
✅ Require status checks to pass
✅ Require branches to be up to date
```

---

## 작동 방식

### 1. 코드 변경 및 Push (main)

```bash
# main 브랜치에서 작업
git checkout main
git add apps/api-service/
git commit -m "feat: add new endpoint"
git push origin main
```

### 2. GitHub Actions 자동 실행

```yaml
# .github/workflows/ci-api-service.yml
# main 브랜치로 push → workflow 트리거
on:
  push:
    branches: [main, develop]
    paths:
      - "apps/api-service/**"
```

### 3. 이미지 빌드 및 ECR Push

```yaml
# .github/workflows/build-and-push.yml
# Docker 이미지 빌드
# ECR에 push: agent-t-dev/api-service:sha-abc1234
```

### 4. Helm Values 자동 업데이트 (gitops/dev)

```yaml
# GitHub Actions가 gitops/dev 브랜치로 checkout
git checkout -B gitops/dev origin/gitops/dev

# values-dev.yaml 업데이트
# image.tag: sha-abc1234

git commit -m "chore(helm): update api-service image to sha-abc1234"
git push origin gitops/dev
```

### 5. Argo CD 자동 배포

```yaml
# infra/argocd/applications/dev/api-service.yaml
spec:
  source:
    repoURL: https://github.com/seol-hj/agent_T.git
    targetRevision: gitops/dev  # ✅ gitops/dev 브랜치 감시
    path: infra/helm/services/api-service
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Argo CD가 `gitops/dev` 브랜치를 3분마다 폴링 → 변경 감지 → 자동 배포

---

## 브랜치 전략

### main 브랜치 (소스 코드)

**용도**: 애플리케이션 소스 코드
**변경**: 개발자 PR → 리뷰 → Merge
**보호**: Branch protection 활성화

```
apps/
├── api-service/
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
└── ...
```

---

### gitops/dev 브랜치 (배포 명세)

**용도**: Helm values (image tag만)
**변경**: GitHub Actions만 push
**보호**: Protection 불필요 (자동화 전용)

```
infra/helm/services/
├── api-service/
│   └── values-dev.yaml  # image.tag 자동 업데이트
├── frontend/
│   └── values-dev.yaml
└── ...
```

---

## 환경별 브랜치 (향후)

### Development
```
소스: main
배포 명세: gitops/dev
Argo CD: targetRevision: gitops/dev
```

### Production (향후)
```
소스: release/v1.x
배포 명세: gitops/prod
Argo CD: targetRevision: gitops/prod
```

---

## 트러블슈팅

### 문제: "gitops/dev 브랜치가 없습니다"

**원인**: 초기 브랜치 미생성

**해결**:
```bash
git checkout main
git checkout -b gitops/dev
git push origin gitops/dev
```

---

### 문제: "GitHub Actions가 gitops/dev에 push 실패"

**원인**: Branch protection 설정

**해결**: gitops/dev 브랜치는 protection 제거
```
Repository → Settings → Branches
→ gitops/dev protection rule 삭제
```

---

### 문제: "Argo CD가 변경을 감지하지 못합니다"

**확인 1**: Application의 targetRevision 확인
```bash
kubectl get application -n argocd api-service -o yaml | grep targetRevision
# 출력: targetRevision: gitops/dev
```

**확인 2**: Argo CD 폴링 간격
```bash
# 기본: 3분마다 폴링
# 수동 동기화
argocd app sync api-service
```

---

### 문제: "main 브랜치에 값 업데이트가 없습니다"

**예상 동작**: 
- main 브랜치: 소스 코드만 (values 변경 없음)
- gitops/dev 브랜치: values만 자동 업데이트

**확인**:
```bash
# gitops/dev 브랜치 확인
git checkout gitops/dev
git log --oneline -5

# 출력:
# abc1234 chore(helm): update api-service image to sha-xyz
# def5678 chore(helm): update frontend image to sha-abc
```

---

## 참고

### GitOps 표준 패턴

**Separation of Concerns**:
- 소스 코드 → main 브랜치
- 배포 명세 → gitops/* 브랜치
- 코드 변경이 배포 명세를 자동 생성

**장점**:
1. Branch protection 우회 불필요
2. 명확한 책임 분리 (코드 vs 배포)
3. 배포 히스토리 추적 가능 (gitops/dev 커밋 로그)
4. 롤백 간편 (git revert)

**단점**:
- 브랜치 관리 필요
- 초기 설정 약간 복잡

---

## 검증

### 1. 브랜치 확인
```bash
git branch -a | grep gitops
# 출력: remotes/origin/gitops/dev
```

### 2. Argo CD Application 확인
```bash
kubectl get application -n argocd -o yaml | grep targetRevision
# 모두 gitops/dev 여야 함
```

### 3. 자동 배포 테스트
```bash
# 1. main에 코드 push
git checkout main
echo "test" >> apps/api-service/README.md
git add .
git commit -m "test: gitops flow"
git push origin main

# 2. GitHub Actions 확인 (2-3분)
# https://github.com/seol-hj/agent_T/actions

# 3. gitops/dev 브랜치 확인
git fetch origin gitops/dev
git log origin/gitops/dev --oneline -1
# 출력: chore(helm): update api-service image to sha-xxx

# 4. Argo CD 동기화 확인 (3분 이내)
kubectl get pods -l app=api-service
```

---

**작성일**: 2026-05-11  
**관련 문서**: 
- [ci-fixes-final-2026-05-11.md](./ci-fixes-final-2026-05-11.md)
- [github-secrets-setup.md](./github-secrets-setup.md)
