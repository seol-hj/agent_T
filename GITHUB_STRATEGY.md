# GitHub 레포지토리 & 브랜치 전략

Agent T 프로젝트의 Git 워크플로우 및 협업 가이드

---

## 📦 레포지토리 구조

### 단일 모노레포 (Monorepo) 사용 ✅

**권장**: 모든 코드를 하나의 레포지토리에 관리

```
agent-t/  (단일 레포)
├── apps/                  # 모든 마이크로서비스
├── libs/                  # 공통 라이브러리
├── infra/                 # Terraform + Helm
├── scripts/               # 자동화 스크립트
└── docs/                  # 문서
```

**장점**:
- ✅ 원자적 커밋 (여러 서비스를 한 번에 변경 가능)
- ✅ 공통 라이브러리 관리 용이
- ✅ CI/CD 파이프라인 단순화
- ✅ 코드 리뷰 및 히스토리 추적 용이
- ✅ 의존성 버전 관리 통일

**단점**:
- ⚠️ 레포지토리 크기 증가 (git clone 느림)
- ⚠️ 권한 관리 세분화 어려움 (팀별로 다른 서비스 담당 시)

---

## 🌿 브랜치 전략: GitHub Flow

**표준 워크플로우**: GitHub Flow (간단하고 효과적)

### 브랜치 구조

```
main (보호)
├── feature/add-simulation-cache
├── feature/frontend-dark-mode
├── bugfix/pipeline-timeout
├── hotfix/memory-leak
└── docs/update-deployment-guide
```

### 브랜치 종류

| 브랜치 타입 | 네이밍 | 용도 | 예시 |
|------------|--------|------|------|
| **main** | `main` | 프로덕션 배포 가능 상태 | - |
| **feature** | `feature/<기능명>` | 새 기능 개발 | `feature/add-llm-cache` |
| **bugfix** | `bugfix/<이슈명>` | 버그 수정 | `bugfix/pipeline-memory-leak` |
| **hotfix** | `hotfix/<긴급수정>` | 프로덕션 긴급 패치 | `hotfix/db-connection-pool` |
| **docs** | `docs/<문서명>` | 문서 업데이트 | `docs/update-readme` |
| **refactor** | `refactor/<대상>` | 리팩토링 (기능 변경 없음) | `refactor/storage-gateway` |

---

## 🔄 워크플로우

### 1. 새 기능 개발

```bash
# 1. main에서 최신 코드 받기
git checkout main
git pull origin main

# 2. feature 브랜치 생성
git checkout -b feature/add-simulation-cache

# 3. 개발 및 커밋
git add apps/simulation-service/cache.py
git commit -m "feat(simulation): add Redis cache for network files"

# 4. 원격 브랜치로 push
git push origin feature/add-simulation-cache

# 5. GitHub에서 Pull Request 생성
# - Base: main
# - Compare: feature/add-simulation-cache
# - 리뷰어 지정
# - 라벨 추가 (enhancement, simulation-service)

# 6. 리뷰 완료 후 Merge
# - Squash and merge (권장)
# - 브랜치 자동 삭제 옵션 활성화

# 7. 로컬 정리
git checkout main
git pull origin main
git branch -d feature/add-simulation-cache
```

### 2. 버그 수정

```bash
# 1. bugfix 브랜치 생성
git checkout -b bugfix/pipeline-timeout

# 2. 수정 및 커밋
git commit -m "fix(pipeline): increase timeout to 300s"

# 3. PR 생성 및 Merge
# (위와 동일)
```

### 3. 핫픽스 (긴급 패치)

```bash
# 프로덕션에 긴급히 배포해야 하는 경우
git checkout -b hotfix/db-connection-pool

# 수정 후 즉시 PR + 리뷰 (간소화)
git commit -m "hotfix(pipeline): fix DB connection pool exhaustion"

# Merge 후 즉시 배포
```

---

## 📝 커밋 메시지 컨벤션

### Conventional Commits 사용

**포맷**:
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Type (필수)

| Type | 설명 | 예시 |
|------|------|------|
| **feat** | 새 기능 추가 | `feat(agent): add LLM response caching` |
| **fix** | 버그 수정 | `fix(pipeline): handle null experiment_id` |
| **docs** | 문서 업데이트 | `docs: update deployment guide` |
| **style** | 코드 포맷팅 (기능 변경 없음) | `style(frontend): fix ESLint warnings` |
| **refactor** | 리팩토링 (기능/버그 변경 없음) | `refactor(storage): simplify S3 upload logic` |
| **test** | 테스트 추가/수정 | `test(simulation): add unit tests for demand builder` |
| **chore** | 빌드/설정 변경 | `chore: upgrade FastAPI to 0.105.0` |
| **perf** | 성능 개선 | `perf(pipeline): optimize DB query` |
| **ci** | CI/CD 변경 | `ci: add GitHub Actions workflow` |

### Scope (선택)

서비스 또는 모듈 이름:
- `pipeline`, `agent`, `simulation`, `analysis`, `report`, `frontend`
- `infra`, `terraform`, `helm`, `argocd`
- `common`, `storage`, `llm`

### Subject (필수)

- 명령형 (imperative mood): "add" (O), "added" (X)
- 소문자 시작
- 마침표 없음
- 50자 이하

### 예시

```bash
# 좋은 예
git commit -m "feat(simulation): add SUMO network caching"
git commit -m "fix(pipeline): prevent duplicate execution IDs"
git commit -m "docs: add troubleshooting section to QUICKSTART"
git commit -m "refactor(frontend): extract API client to separate file"

# 나쁜 예
git commit -m "updated code"  # 너무 모호
git commit -m "Fixed bug"     # type/scope 없음
git commit -m "Added new feature for simulation service that caches network files"  # 너무 김
```

---

## 🔒 브랜치 보호 규칙

### main 브랜치 보호 설정

GitHub Repository Settings → Branches → Branch protection rules:

**필수 설정**:
- ✅ Require a pull request before merging
  - ✅ Require approvals: 1명 이상
  - ✅ Dismiss stale reviews when new commits are pushed
- ✅ Require status checks to pass before merging
  - ✅ CI (GitHub Actions)
  - ✅ Lint checks
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings (Admin 포함)

**선택 설정**:
- Require linear history (Squash merge 강제)
- Require signed commits (보안 강화)

---

## 🚀 배포 워크플로우

### CI/CD 자동화

```
코드 변경 (PR)
    ↓
GitHub Actions (CI)
    ├── Lint (ruff, ESLint)
    ├── Unit Tests
    ├── Build Docker Images
    └── Security Scan (Trivy)
    ↓
PR Merge to main
    ↓
GitHub Actions (CD)
    ├── Build & Push to ECR
    ├── Update Helm values (image tag)
    └── Git commit & push
    ↓
Argo CD (자동 감지)
    ├── Sync from Git
    └── Deploy to EKS
    ↓
Production
```

### 환경별 배포 전략

| 환경 | 브랜치 | 배포 방식 | 승인 |
|------|--------|----------|------|
| **Dev** | `main` | Auto (Argo CD) | 불필요 |
| **Staging** | `main` (tag) | Auto | 불필요 |
| **Production** | `main` (release tag) | Manual | 필수 |

**Release 태그**:
```bash
# Semantic Versioning 사용
git tag -a v0.4.0 -m "Release v0.4.0"
git push origin v0.4.0

# Production 배포 트리거
```

---

## 👥 협업 가이드

### Pull Request 작성

**제목**:
- 커밋 메시지와 동일한 형식
- `feat(simulation): add Redis caching for network files`

**Description 템플릿**:
```markdown
## 변경 내용
- SUMO 네트워크 파일에 Redis 캐싱 추가
- TTL 1시간 설정
- Cache miss 시 자동으로 S3에서 로드

## 동기
OpenStreetMap 다운로드가 느려서 동일한 지역의 시뮬레이션이 반복될 때 비효율적

## 테스트
- [x] Unit tests 추가
- [x] 로컬 Docker Compose 테스트
- [ ] AWS Dev 환경 테스트 (배포 후)

## Breaking Changes
없음

## 관련 이슈
Closes #123
```

### 코드 리뷰 체크리스트

**리뷰어가 확인할 사항**:
- [ ] 코드가 요구사항을 충족하는가?
- [ ] 테스트가 충분한가?
- [ ] 문서가 업데이트되었는가?
- [ ] 보안 이슈가 없는가? (secrets, SQL injection 등)
- [ ] 성능에 영향이 없는가?
- [ ] Breaking change가 있다면 명확히 표시되었는가?

### Merge 방식

**Squash and merge** 권장:
- Feature 브랜치의 여러 커밋을 하나로 합침
- main 브랜치 히스토리가 깔끔해짐
- Revert가 쉬움

**Merge commit** 사용 시:
- 여러 사람이 함께 작업한 큰 feature
- 커밋 히스토리를 보존해야 하는 경우

---

## 📊 릴리스 관리

### Semantic Versioning

**버전 형식**: `v<major>.<minor>.<patch>`

| 변경 타입 | 버전 | 예시 |
|----------|------|------|
| Breaking change | Major | `v1.0.0` → `v2.0.0` |
| 새 기능 추가 (호환성 유지) | Minor | `v1.0.0` → `v1.1.0` |
| 버그 수정 | Patch | `v1.0.0` → `v1.0.1` |

### Release 프로세스

```bash
# 1. CHANGELOG.md 업데이트
vim CHANGELOG.md

# 2. 버전 태그 생성
git tag -a v0.5.0 -m "Release v0.5.0

- feat: Add LLM response caching
- feat: Add Redis support
- fix: Pipeline timeout issue
- docs: Update deployment guide
"

# 3. 태그 푸시
git push origin v0.5.0

# 4. GitHub Release 생성
# - GitHub UI에서 Release 생성
# - 자동으로 Release Notes 생성
# - Docker 이미지 첨부 (선택)
```

---

## 📂 .gitignore

**절대 커밋 금지**:
```gitignore
# Secrets
.env
.env.local
*.pem
*.key
*_rsa
secrets/

# Terraform
*.tfstate
*.tfstate.backup
.terraform/
terraform.tfvars

# Python
__pycache__/
*.pyc
.venv/
venv/

# Node.js
node_modules/
.next/
out/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Data
/data/
*.sql
```

---

## ✅ 체크리스트

### 새 기여자 온보딩
- [ ] 레포지토리 Fork
- [ ] 로컬 클론 및 Docker Compose 실행
- [ ] Feature 브랜치 생성
- [ ] 커밋 메시지 컨벤션 숙지
- [ ] PR 템플릿 사용
- [ ] 첫 PR 제출 (문서 수정 추천)

### 커밋 전 확인
- [ ] 린트 통과 (`ruff check`, `npm run lint`)
- [ ] 테스트 통과 (`./scripts/test-services-local.sh`)
- [ ] 커밋 메시지 컨벤션 준수
- [ ] Secrets 포함 여부 확인 (`git diff`)

### PR 생성 전 확인
- [ ] main 브랜치 최신 코드 반영 (`git rebase main`)
- [ ] 충돌 해결
- [ ] Description 템플릿 작성
- [ ] 관련 이슈 링크
- [ ] 라벨 추가

---

## 📚 참고 자료

- **Conventional Commits**: https://www.conventionalcommits.org/
- **GitHub Flow**: https://githubflow.github.io/
- **Semantic Versioning**: https://semver.org/
- **Git Best Practices**: https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project

---

**작성일**: 2026-05-10  
**버전**: 0.4.0
