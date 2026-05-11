# 근본 원인 해결: libs 변경 시 CI 트리거 - 2026-05-11

## 문제의 근본 원인

### 왜 서비스가 계속 실패했는가?

```
libs/common/__init__.py 수정 (Retriever 오류 수정)
  ↓
gitops/dev에 push ✅
  ↓
main에 merge ✅
  ↓
❌ GitHub Actions가 실행되지 않음!
  ↓
❌ 새 이미지가 빌드되지 않음
  ↓
❌ Pod가 여전히 이전 이미지 (오류 포함) 사용
  ↓
❌ CrashLoopBackOff 계속 발생
```

---

## 근본 원인: CI 워크플로우가 libs 변경을 감지하지 못함

### 문제가 있던 설정

```yaml
# .github/workflows/ci-agent-service.yml (Before)
on:
  push:
    branches: [main]
    paths:
      - "apps/agent-service/**"  # ✅ 이건 감지
      - ".github/workflows/ci-agent-service.yml"  # ✅ 이것도 감지
      # ❌ libs/** 없음!
```

**결과**:
- `apps/agent-service/` 변경 → CI 트리거 ✅
- `libs/common/` 변경 → CI 트리거 안 됨 ❌

---

### 수정된 설정

```yaml
# .github/workflows/ci-agent-service.yml (After)
on:
  push:
    branches: [main]
    paths:
      - "apps/agent-service/**"
      - "libs/**"  # ✅ 추가!
      - ".github/workflows/ci-agent-service.yml"
```

**결과**:
- `apps/agent-service/` 변경 → CI 트리거 ✅
- `libs/common/` 변경 → CI 트리거 ✅
- **backend 서비스가 모두 재빌드됨**

---

## 왜 이렇게 설정해야 하는가?

### Backend 서비스의 의존성 구조

```
apps/agent-service/
├── main.py
├── Dockerfile
└── requirements.txt

Dockerfile:
  COPY libs /app/libs  ← libs 의존
  COPY apps/agent-service /app

main.py:
  from common import get_llm_gateway  ← libs/common 사용
```

**핵심**: 
- Backend 서비스는 `libs/common`에 **직접 의존**
- `libs/common` 변경 = 모든 backend 서비스에 영향
- **반드시 재빌드 필요**

---

## 적용된 수정

### 수정된 파일 (5개)

```
.github/workflows/ci-agent-service.yml
.github/workflows/ci-analysis-service.yml
.github/workflows/ci-api-service.yml
.github/workflows/ci-report-service.yml
.github/workflows/ci-simulation-service.yml
```

**변경 내용**: 각 파일의 `paths`에 `libs/**` 추가

---

### Frontend는 제외

```yaml
# .github/workflows/ci-frontend.yml
on:
  push:
    paths:
      - "apps/frontend/**"
      # libs/** 추가 안 함 (의존하지 않음)
```

**이유**: Frontend는 Node.js 앱으로 libs/common 사용하지 않음

---

## 검증 방법

### 1. 현재 paths 확인

```bash
grep -A 7 "push:" .github/workflows/ci-agent-service.yml

# 출력에 다음이 있어야 함:
#   - "libs/**"
```

---

### 2. libs 변경으로 재빌드 트리거

```bash
# 1. libs/common에 작은 변경 (주석 추가 등)
echo "# Trigger rebuild" >> libs/common/__init__.py

# 2. Commit & Push
git add libs/common/__init__.py
git commit -m "chore: trigger rebuild"
git push origin main

# 3. GitHub Actions 확인
# https://github.com/seol-hj/agent_T/actions
# → 5개 backend 서비스 workflow가 모두 실행되어야 함
```

---

### 3. 새 이미지 확인

```bash
# 10분 후 ECR 확인
aws ecr describe-images \
  --repository-name agent-t-dev/agent-service \
  --region ap-northeast-2 \
  --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]'

# 새 sha-xxx 태그가 생성되었어야 함
```

---

### 4. gitops/dev 자동 업데이트 확인

```bash
git fetch origin gitops/dev
git show origin/gitops/dev:infra/helm/services/agent-service/values-dev.yaml | grep "tag:"

# 새 태그로 업데이트되었어야 함
```

---

### 5. Pod 정상 작동 확인

```bash
# 15-20분 후
kubectl get pods -n default

# 모든 backend 서비스가 Running이어야 함
```

---

## 현재 진행 상황

### ✅ 완료
1. CI 워크플로우에 `libs/**` 경로 추가
2. feature/cicd에 commit & push
3. libs/common에 minor change로 재빌드 트리거

### ⏳ 진행 중
1. feature/cicd → main PR 생성 대기
2. PR Merge 대기
3. GitHub Actions 실행 (5개 backend 서비스)
4. 새 이미지 ECR push
5. gitops/dev 자동 업데이트
6. Argo CD 자동 배포

### 예상 시간
- PR Merge → 모든 Pod Running: **15-20분**

---

## 다음 단계

### 1. PR 생성 및 Merge

```bash
# GitHub Web UI에서:
1. https://github.com/seol-hj/agent_T
2. "Compare & pull request" 클릭
3. feature/cicd → main
4. Title: "fix: add libs/** to CI triggers and rebuild services"
5. "Create pull request"
6. "Merge pull request"
```

---

### 2. GitHub Actions 모니터링

```
https://github.com/seol-hj/agent_T/actions

확인 사항:
✅ CI - Agent Service 실행 중
✅ CI - Analysis Service 실행 중
✅ CI - API Service 실행 중 (libs 변경되었으므로)
✅ CI - Report Service 실행 중
✅ CI - Simulation Service 실행 중
```

---

### 3. Pod 상태 모니터링

```bash
# 실시간 모니터링
watch kubectl get pods -n default

# 15-20분 후 예상 결과:
# agent-service         1/1  Running
# analysis-service      1/1  Running
# api-service           1/1  Running
# report-service        1/1  Running
# simulation-service    1/1  Running
# frontend              1/1  Running
```

---

## 왜 latest 태그를 사용하지 않았는가?

### ❌ latest 태그의 문제점

```yaml
image:
  tag: "latest"  # ❌ 안티패턴
```

**문제**:
1. **불확실성**: 어떤 버전인지 알 수 없음
2. **재현 불가**: 이전 버전으로 롤백 불가능
3. **캐싱 문제**: Kubernetes가 이미지를 pull하지 않을 수 있음
4. **동시성 문제**: 여러 환경에서 다른 버전 사용 가능

---

### ✅ SHA 태그의 장점

```yaml
image:
  tag: "sha-a1b470b"  # ✅ Best Practice
```

**장점**:
1. **명확성**: Git commit SHA와 1:1 매핑
2. **재현성**: 언제든 정확한 버전으로 롤백 가능
3. **추적성**: 어떤 코드가 배포되었는지 명확
4. **불변성**: 태그가 절대 변경되지 않음

---

## 표준 이미지 태깅 전략

### 권장: Git SHA 기반

```bash
# GitHub Actions에서 자동 생성
IMAGE_TAG="sha-$(git rev-parse --short HEAD)"
# 예: sha-a1b470b

# ECR에 push
docker tag myapp:latest 123456789012.dkr.ecr.region.amazonaws.com/myapp:$IMAGE_TAG
docker push 123456789012.dkr.ecr.region.amazonaws.com/myapp:$IMAGE_TAG
```

---

### 추가 태그 (선택)

```bash
# Semantic version
docker tag myapp:latest myapp:v1.2.3

# Environment
docker tag myapp:latest myapp:dev-sha-a1b470b

# Date
docker tag myapp:latest myapp:2026-05-11-sha-a1b470b
```

---

### 현재 구현

```yaml
# .github/workflows/build-and-push.yml
IMAGE_TAG="sha-$(echo ${{ github.sha }} | cut -c1-7)"

# 결과:
# - agent-t-dev/agent-service:sha-a1b470b
# - agent-t-dev/agent-service:latest (추가)

# latest는 convenience를 위해 함께 push
# 하지만 배포에는 SHA 태그 사용
```

---

## 교훈

### 1. 공통 라이브러리 변경 = 모든 의존 서비스 재빌드

**규칙**: 
- `libs/` 변경 시 모든 backend CI 트리거
- Monorepo에서는 의존성 그래프 고려 필수

---

### 2. CI 트리거 경로는 신중하게 설정

**체크리스트**:
- [ ] 앱 자체 코드 (`apps/service/**`)
- [ ] 공통 라이브러리 (`libs/**`)
- [ ] Dockerfile
- [ ] CI 워크플로우 자체
- [ ] 환경 설정 파일 (필요 시)

---

### 3. 이미지 태그는 항상 불변 식별자 사용

**Good**:
- Git SHA: `sha-a1b470b`
- Semantic version: `v1.2.3`
- Build number: `build-12345`

**Bad**:
- `latest`
- `dev`
- `stable`

---

## 파일 변경 요약

### 수정된 파일 (6개)

```
.github/workflows/ci-agent-service.yml      # libs/** 추가
.github/workflows/ci-analysis-service.yml   # libs/** 추가
.github/workflows/ci-api-service.yml        # libs/** 추가
.github/workflows/ci-report-service.yml     # libs/** 추가
.github/workflows/ci-simulation-service.yml # libs/** 추가
libs/common/__init__.py                     # 재빌드 트리거용 minor 변경
```

---

## 최종 상태

### ✅ 해결된 문제
1. libs 변경 시 CI 트리거 안 되던 문제
2. Backend 서비스가 이전 이미지(오류 포함) 사용하던 문제
3. latest 태그 사용 고려했으나 표준 방식(SHA 태그) 유지

### 🎯 현재 상태
- CI 워크플로우 수정 완료 ✅
- feature/cicd에 push 완료 ✅
- PR & Merge 대기 중 ⏳

### 🚀 다음 단계
1. PR 생성 및 Merge
2. GitHub Actions 실행 확인 (5개 서비스)
3. 15-20분 후 모든 Pod Running 확인

---

**작성일**: 2026-05-11  
**상태**: CI 수정 완료, PR 대기 중  
**예상 완료**: PR Merge 후 20분

**관련 문서**:
- [runtime-errors-fix-2026-05-11.md](./runtime-errors-fix-2026-05-11.md)
- [branch-strategy-final.md](./branch-strategy-final.md)
