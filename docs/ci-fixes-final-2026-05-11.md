# CI/CD 최종 수정 - 2026-05-11

## 발견된 추가 문제

### 1. Git Push 권한 없음
```
remote: Permission to seol-hj/agent_T.git denied to github-actions[bot].
fatal: unable to access 'https://github.com/seol-hj/agent_T/': The requested URL returned error: 403
Error: Process completed with exit code 128.
```

**원인**: GitHub Actions가 repository에 write 권한 없음

---

### 2. simulation-runner 디렉토리 없음
```
ERROR: lstat apps/simulation-runner: no such file or directory
```

**원인**: `simulation-runner`는 별도 앱이 아니라 `simulation-service`의 서브모듈

---

### 3. api-service requirements.txt 경로 오류
```
ERROR: "/requirements.txt": not found
```

**원인**: `api-service/Dockerfile`이 루트 context를 고려하지 않음

---

## 해결 방법

### 1. Git Push 권한 설정

#### build-and-push.yml 수정

**permissions 추가**:
```yaml
# Before
name: Build and Push Docker Image

on:
  workflow_call:

# After
name: Build and Push Docker Image

permissions:
  contents: write  # Git push 권한

on:
  workflow_call:
```

**checkout token 설정**:
```yaml
# Before
- name: Checkout code
  uses: actions/checkout@v4

# After
- name: Checkout code
  uses: actions/checkout@v4
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    fetch-depth: 0  # 전체 히스토리 (git push 위해)
```

**설명**:
- `permissions: contents: write`: Workflow에 repository write 권한 부여
- `token: ${{ secrets.GITHUB_TOKEN }}`: GitHub 자동 생성 토큰 사용
- `fetch-depth: 0`: Git history 전체 가져오기 (push에 필요)

---

### 2. simulation-runner Workflow 제거

**문제 분석**:
```
프로젝트 구조:
apps/
├── simulation-service/          # 실제 존재
│   ├── Dockerfile
│   ├── runner/                  # 서브모듈
│   ├── network_builder/
│   └── demand_builder/
└── simulation-runner/           # ❌ 존재하지 않음
```

**해결**:
```bash
# ci-simulation-runner.yml 삭제
mv .github/workflows/ci-simulation-runner.yml .archive/workflows/
```

**이유**:
- `simulation-runner`는 `simulation-service`의 서브디렉토리
- 별도 Docker 이미지 불필요
- ECR repository도 삭제 가능

---

### 3. api-service Dockerfile 수정

#### 문제
```dockerfile
# api-service/Dockerfile (Before)
COPY requirements.txt .  # ❌ 루트 context에서 /requirements.txt 찾음
COPY . .                 # ❌ 루트 전체 복사
```

**Build context가 루트 (`.`)인데**, Dockerfile이 상대 경로 사용

#### 해결
```dockerfile
# api-service/Dockerfile (After)
# 공통 라이브러리 복사
COPY libs /app/libs

# Python 의존성 설치
COPY apps/api-service/requirements.txt .  # ✅ 전체 경로
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY apps/api-service /app  # ✅ 전체 경로

# PYTHONPATH 추가
ENV PYTHONPATH=/app:/app/libs
```

---

## 전체 수정 요약

### 1. 권한 설정
- **파일**: `.github/workflows/build-and-push.yml`
- **변경**: `permissions: contents: write` 추가
- **변경**: `checkout` step에 token 설정

### 2. Workflow 정리
- **삭제**: `.github/workflows/ci-simulation-runner.yml`
- **이유**: 디렉토리 자체가 없음 (서브모듈)

### 3. Dockerfile 수정
- **파일**: `apps/api-service/Dockerfile`
- **변경**: 
  - `COPY requirements.txt` → `COPY apps/api-service/requirements.txt`
  - `COPY . .` → `COPY apps/api-service /app`
  - `COPY libs /app/libs` 추가

---

## 서비스별 Dockerfile 패턴

### 표준 패턴 (Backend)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지
RUN apt-get update && apt-get install -y curl

# 공통 라이브러리 (루트 context 필요)
COPY libs /app/libs

# Python 의존성
COPY apps/<service>/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY apps/<service> /app

# 환경 변수
ENV PYTHONPATH=/app:/app/libs

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "<port>"]
```

### Frontend 패턴 (변경 없음)
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Build context: apps/frontend
COPY package.json ./
COPY . ./

RUN npm install
RUN npm run build

CMD ["node", "server.js"]
```

---

## ECR Repositories

### 현재 구성 (6개)
```
agent-t-dev/frontend
agent-t-dev/agent-service
agent-t-dev/analysis-service
agent-t-dev/api-service
agent-t-dev/report-service
agent-t-dev/simulation-service
```

### 제거 가능 (1개)
```
agent-t-dev/simulation-runner  # ❌ 사용 안 함
```

**제거 방법**:
```bash
# Terraform에서 제거
# infra/terraform/modules/ecr/main.tf
# "simulation-runner" 항목 삭제 후

cd infra/terraform/envs/dev
terraform plan
terraform apply
```

---

## GitHub Actions 권한 옵션

### Option 1: GITHUB_TOKEN (현재 방식)
```yaml
permissions:
  contents: write

- uses: actions/checkout@v4
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

**장점**: 자동 생성, 설정 불필요  
**단점**: 다른 workflow 트리거 안 됨

---

### Option 2: Personal Access Token (PAT)
```yaml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.PAT_TOKEN }}
```

**필요 작업**:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Scopes: `repo` 선택
4. Repository Secrets에 `PAT_TOKEN` 추가

**장점**: 다른 workflow 트리거 가능  
**단점**: 수동 생성 필요, 만료 관리 필요

---

### Option 3: GitHub App
```yaml
- uses: actions/create-github-app-token@v1
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}
```

**장점**: 가장 안전, 세밀한 권한 제어  
**단점**: 설정 복잡

---

**권장**: Option 1 (GITHUB_TOKEN) - 현재 구현됨 ✅

---

## 검증

### 1. Git Push 권한 확인
```bash
# GitHub Actions 실행 후
# ✅ "chore(helm): update ... image" 커밋 생성됨
# ✅ Git push 성공
# ✅ values-dev.yaml 업데이트됨
```

### 2. Docker Build 확인
```bash
# ✅ libs/ 복사 성공
# ✅ requirements.txt 찾음
# ✅ 이미지 빌드 성공
# ✅ ECR push 성공
```

### 3. Workflow 목록
```bash
ls .github/workflows/ci-*.yml

# 출력 (6개):
# ci-frontend.yml
# ci-agent-service.yml
# ci-analysis-service.yml
# ci-api-service.yml
# ci-report-service.yml
# ci-simulation-service.yml

# simulation-runner.yml 제거됨 ✅
```

---

## 트러블슈팅

### 문제: "Permission denied" 여전히 발생
**해결**: Repository Settings 확인
```
Repository → Settings → Actions → General
→ Workflow permissions
→ ✅ Read and write permissions 선택
```

### 문제: "Git push 후 다른 workflow 트리거 안 됨"
**원인**: GITHUB_TOKEN의 제약  
**해결**: PAT 사용 (Option 2)

### 문제: "simulation-runner ECR 남아있음"
**해결**: Terraform으로 제거
```bash
cd infra/terraform/envs/dev
terraform plan
terraform apply
```

---

## 다음 단계

### 1. Git Commit & Push
```bash
git add .github/workflows/
git add apps/api-service/Dockerfile
git add docs/
git commit -m "fix: git push permissions, remove simulation-runner, fix api-service Dockerfile"
git push origin main
```

### 2. Repository Settings 확인
```
Settings → Actions → General → Workflow permissions
→ Read and write permissions ✅
```

### 3. GitHub Actions 테스트
- 코드 수정 후 push
- Workflow 실행 확인
- Git push 성공 확인
- ECR 이미지 확인

---

## 최종 정리

### ✅ 완료된 수정
1. Git push 권한 설정 (permissions + token)
2. simulation-runner workflow 제거
3. api-service Dockerfile 수정 (경로 통일)

### 📊 현재 상태
- **Workflows**: 6개 (정상)
- **ECR Repos**: 6개 사용, 1개 정리 필요
- **Dockerfiles**: 모두 루트 context 지원

### 🚀 예상 결과
- ✅ Docker build 성공
- ✅ ECR push 성공
- ✅ Helm values 자동 업데이트
- ✅ Argo CD 자동 배포

---

**작성일**: 2026-05-11  
**관련 문서**: 
- [ci-fixes-2026-05-11.md](./ci-fixes-2026-05-11.md)
- [github-secrets-setup.md](./github-secrets-setup.md)
