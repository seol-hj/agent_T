# CI/CD Pipeline

Agent T 프로젝트의 **CI/CD 파이프라인 구성 및 배포 흐름**을 설명한다.

---

## 개요

```
   개발자 코드 변경 (PR)
       │
       ▼
 ┌─────────────────────────────────────┐
 │     GitHub Actions (CI)              │
 │  ✓ Path filter (변경된 서비스만)     │
 │  ✓ Lint & Test                       │
 │  ✓ Docker Build                      │
 │  ✓ ECR Push (sha-<short-sha>)        │
 │  ✓ Terraform Plan (PR)               │
 └──────────────┬──────────────────────┘
                │
                ▼ (main 브랜치 merge)
 ┌─────────────────────────────────────┐
 │           Argo CD (CD)               │
 │  ✓ Git → Cluster 동기화              │
 │  ✓ Auto Sync + Self Heal (dev)       │
 │  ✓ Manual Sync (prod)                │
 │  ✓ Application Health Check          │
 └──────────────┬──────────────────────┘
                │
                ▼
         EKS Cluster (dev/prod)
            ├── api-service
            ├── agent-service
            ├── simulation-service
            ├── analysis-service
            └── report-service
```

---

## CI (GitHub Actions)

### 워크플로우 목록

| 워크플로우 | 트리거 | 목적 |
|---|---|---|
| `ci-api-service.yml` | `apps/api-service/**` 변경 | API Service 빌드 및 테스트 |
| `ci-agent-service.yml` | `apps/agent-service/**` 변경 | Agent Service 빌드 및 테스트 |
| `ci-simulation-service.yml` | `apps/simulation-service/**` 변경 | Simulation Service 빌드 |
| `ci-analysis-service.yml` | `apps/analysis-service/**` 변경 | Analysis Service 빌드 |
| `ci-report-service.yml` | `apps/report-service/**` 변경 | Report Service 빌드 |
| `ci-simulation-runner.yml` | `apps/simulation-runner/**` 변경 | SUMO Runner 이미지 빌드 |
| `ci-frontend.yml` | `apps/frontend/**` 변경 | Frontend 빌드 |
| `terraform-plan.yml` | `infra/terraform/**` 변경 (PR) | Terraform 검증 및 Plan |
| `terraform-apply.yml` | 수동 트리거 (workflow_dispatch) | Terraform Apply (승인 필요) |

### Path Filter (변경 감지)

각 서비스 워크플로우는 **해당 서비스 디렉토리 변경 시에만 실행**된다.

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - "apps/api-service/**"
      - ".github/workflows/ci-api-service.yml"
  pull_request:
    branches: [main, develop]
    paths:
      - "apps/api-service/**"
```

**장점**:
- Monorepo에서 불필요한 빌드 방지
- CI 시간 단축
- 리소스 절약

### 브랜치 전략

| 브랜치 | 용도 | 배포 환경 |
|---|---|---|
| `develop` | 개발 브랜치 | dev |
| `main` | 프로덕션 브랜치 | prod |

**흐름**:
1. `feature/*` → `develop` PR
2. `develop` 브랜치 push → dev 환경 배포
3. `develop` → `main` PR (릴리즈)
4. `main` 브랜치 push → prod 환경 배포

### Docker 이미지 빌드 및 Push

#### 1. Reusable Workflow

모든 서비스가 공통으로 사용하는 재사용 가능한 workflow:

```yaml
# .github/workflows/build-and-push.yml
name: Build and Push Docker Image

on:
  workflow_call:
    inputs:
      service-name: ...
      dockerfile-path: ...
      context-path: ...
      ecr-repository: ...
    secrets:
      aws-access-key-id: ...
      aws-secret-access-key: ...
```

**단계**:
1. Checkout code
2. Configure AWS credentials
3. Login to ECR
4. Extract metadata (git SHA)
5. Run tests (optional)
6. Build Docker image
7. Push to ECR (`sha-<short-sha>`, `latest`)

#### 2. 이미지 태그 전략

```
<ecr-registry>/<repository>:sha-<short-sha>
<ecr-registry>/<repository>:latest
```

예시:
```
123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service:sha-a1b2c3d
123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service:latest
```

**주의**:
- `latest` 태그는 CI에서 자동으로 push하지만, **Helm values에서는 사용하지 않음**
- Helm values는 항상 명시적 SHA 태그 사용

#### 3. 환경별 ECR Repository

| 브랜치 | 환경 | ECR Repository |
|---|---|---|
| `develop` | dev | `agent-t-dev/<service>` |
| `main` | prod | `agent-t-prod/<service>` |

워크플로우에서 자동 판별:
```yaml
- name: Determine environment
  id: env
  run: |
    if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
      echo "ecr-repo=agent-t-prod/api-service" >> $GITHUB_OUTPUT
    else
      echo "ecr-repo=agent-t-dev/api-service" >> $GITHUB_OUTPUT
    fi
```

### 테스트 실행

각 서비스 워크플로우에서 테스트 실행:

```yaml
test-command: |
  pip install -r requirements.txt
  pip install pytest pytest-cov
  pytest tests/ --cov=app --cov-report=xml
```

**PR 시**:
- 빌드 검증만 (ECR push 없음)
- 테스트 실행

**main/develop push 시**:
- 테스트 실행
- Docker 빌드
- ECR push

### Terraform CI/CD

#### 1. Terraform Plan (PR 시)

```yaml
# .github/workflows/terraform-plan.yml
on:
  pull_request:
    paths:
      - "infra/terraform/**"
```

**단계**:
1. Terraform fmt check
2. Terraform init
3. Terraform validate
4. Terraform plan
5. PR에 Plan 결과 코멘트

**환경별 Matrix**:
```yaml
strategy:
  matrix:
    environment: [dev, prod]
```

#### 2. Terraform Apply (수동 승인)

```yaml
# .github/workflows/terraform-apply.yml
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, prod]
      auto-approve:
        type: boolean
        default: false
```

**단계**:
1. Terraform init
2. Terraform plan
3. **Manual Approval** (GitHub Issue로 승인 요청)
4. Terraform apply

**수동 승인**:
- GitHub repo admins만 승인 가능
- Issue 생성 → 승인자가 코멘트로 승인
- 승인 후 자동으로 apply 진행

### GitHub Secrets

| Secret | 용도 |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS 인증 (ECR push, Terraform) |
| `AWS_SECRET_ACCESS_KEY` | AWS 인증 |
| `GITHUB_TOKEN` | PR 코멘트, Issue 생성 (자동 제공) |

**설정**:
```bash
# GitHub Repository Settings → Secrets and variables → Actions
# Add repository secret
```

---

## CD (Argo CD)

### GitOps 원칙

**Git = Single Source of Truth**

- 클러스터에서 직접 수정 금지 (`kubectl edit` 금지)
- 모든 변경은 Git PR/MR을 통해 진행
- Argo CD가 Git 변경 사항을 자동으로 클러스터에 반영

### Application 구조

```
infra/argocd/
├── applications/          # 개별 서비스 Application
│   ├── api-service.yaml
│   ├── agent-service.yaml
│   ├── simulation-service.yaml
│   ├── analysis-service.yaml
│   └── report-service.yaml
└── applicationsets/       # ApplicationSet (여러 서비스 일괄 관리)
    └── services.yaml
```

### Sync Policy

#### dev 환경

```yaml
syncPolicy:
  automated:
    prune: true       # Git에서 삭제된 리소스 자동 삭제
    selfHeal: true    # 클러스터에서 변경된 리소스 자동 복구
```

**자동 동기화**:
- Git 변경 사항을 3분마다 polling
- 변경 감지 시 자동으로 클러스터에 반영
- 개발 속도 우선

#### prod 환경

```yaml
syncPolicy: {}
```

**수동 동기화**:
- Git 변경 사항을 감지하지만 자동으로 반영하지 않음
- 운영자가 Argo CD UI/CLI에서 수동으로 Sync 버튼 클릭
- 안전성 우선

### Notification (Slack 연동)

Argo CD는 배포 성공/실패 시 Slack으로 알림 전송.

```yaml
# values-prod.yaml
notifications:
  enabled: true
  triggers:
    trigger.on-deployed: |
      - when: app.status.operationState.phase in ['Succeeded']
        send: [app-deployed]
    trigger.on-sync-failed: |
      - when: app.status.operationState.phase in ['Error', 'Failed']
        send: [app-sync-failed]
```

---

## 배포 흐름

### 1. 개발 환경 (dev) 배포

```
개발자 코드 변경 (apps/api-service/)
       │
       ▼
feature 브랜치 → develop PR
       │
       ▼
GitHub Actions CI
  ✓ Path filter (api-service 변경 감지)
  ✓ Build validation (Docker build, test)
       │
       ▼
PR 승인 & Merge → develop
       │
       ▼
GitHub Actions CI
  ✓ Docker build
  ✓ ECR push (sha-a1b2c3d)
  ✓ Image tag: agent-t-dev/api-service:sha-a1b2c3d
       │
       ▼
(수동) Helm values 업데이트
  ✓ infra/helm/services/api-service/values-dev.yaml
  ✓ image.tag: sha-a1b2c3d
  ✓ Git commit & push
       │
       ▼
Argo CD
  ✓ Git 변경 감지 (3분 polling)
  ✓ Auto sync (dev 환경)
  ✓ Helm install/upgrade
       │
       ▼
EKS dev 클러스터 배포 완료
  ✓ Slack 알림
```

### 2. 프로덕션 환경 (prod) 배포

```
develop → main PR (릴리즈)
       │
       ▼
GitHub Actions CI
  ✓ Terraform plan (인프라 변경 있을 경우)
  ✓ Build validation
       │
       ▼
PR 승인 & Merge → main
       │
       ▼
GitHub Actions CI
  ✓ Docker build
  ✓ ECR push (sha-x7y8z9a)
  ✓ Image tag: agent-t-prod/api-service:sha-x7y8z9a
       │
       ▼
(수동) Helm values 업데이트
  ✓ infra/helm/services/api-service/values-prod.yaml
  ✓ image.tag: sha-x7y8z9a
  ✓ Git commit & push
       │
       ▼
Argo CD
  ✓ Git 변경 감지
  ✓ Manual sync (운영자 승인 필요)
       │
       ▼
운영자 Argo CD UI에서 Sync 버튼 클릭
       │
       ▼
EKS prod 클러스터 배포 완료
  ✓ Slack 알림
```

### 3. Terraform 인프라 변경

```
Terraform 코드 변경 (infra/terraform/)
       │
       ▼
feature 브랜치 → main PR
       │
       ▼
GitHub Actions (terraform-plan.yml)
  ✓ Terraform fmt check
  ✓ Terraform validate
  ✓ Terraform plan (dev, prod)
  ✓ PR에 Plan 결과 코멘트
       │
       ▼
PR 승인 & Merge → main
       │
       ▼
(수동) GitHub Actions (terraform-apply.yml)
  ✓ Workflow dispatch 트리거
  ✓ Environment 선택 (dev / prod)
  ✓ Terraform plan
  ✓ Manual approval (GitHub Issue)
       │
       ▼
승인자가 Issue에서 승인
       │
       ▼
Terraform apply 실행
       │
       ▼
인프라 변경 완료
```

---

## Helm Values 업데이트 (TODO)

현재는 **수동으로 Helm values의 image tag를 업데이트**해야 한다.

### 수동 업데이트

```bash
# 1. ECR에서 최신 이미지 태그 확인
aws ecr describe-images --repository-name agent-t-dev/api-service --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]'

# 2. Helm values 수정
vi infra/helm/services/api-service/values-dev.yaml
# image.tag: sha-a1b2c3d

# 3. Git commit & push
git add infra/helm/services/api-service/values-dev.yaml
git commit -m "chore: update api-service image tag to sha-a1b2c3d"
git push origin develop
```

### 자동 업데이트 (향후 구현)

GitHub Actions에서 ECR push 후 자동으로 Helm values 업데이트:

```yaml
# .github/workflows/ci-api-service.yml
jobs:
  update-helm-values:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Update Helm values
        run: |
          IMAGE_TAG="${{ needs.build-and-push.outputs.image-tag }}"
          yq eval ".image.tag = \"$IMAGE_TAG\"" -i infra/helm/services/api-service/values-dev.yaml

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add infra/helm/services/api-service/values-dev.yaml
          git commit -m "chore: update api-service image tag to $IMAGE_TAG [skip ci]"
          git push
```

**주의**:
- `[skip ci]` 플래그로 무한 루프 방지
- Bot 계정으로 commit

---

## 보안

### 1. GitHub Secrets 관리

- AWS Access Key는 **최소 권한 원칙** (Least Privilege) 적용
- ECR push, Terraform 실행에 필요한 권한만 부여
- 주기적으로 Key rotation

### 2. ECR Image Scanning

ECR에서 자동으로 이미지 취약점 스캔:

```hcl
# infra/terraform/modules/ecr/main.tf
resource "aws_ecr_repository" "this" {
  image_scanning_configuration {
    scan_on_push = true
  }
}
```

### 3. Trivy Scan (Optional)

GitHub Actions에서 Trivy로 이미지 스캔:

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.meta.outputs.image-uri }}
    format: 'sarif'
    output: 'trivy-results.sarif'

- name: Upload Trivy results to GitHub Security tab
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
```

---

## 모니터링

### 1. GitHub Actions 로그

- Workflow 실행 결과 확인: https://github.com/YOUR_ORG/agent-t/actions
- 실패 시 Slack 알림 (추가 구성 필요)

### 2. Argo CD UI

- Application 상태 확인: https://argocd.prod.agent-t.com
- Sync 상태, Health 상태, Event 확인

### 3. ECR 이미지 목록

```bash
aws ecr describe-images --repository-name agent-t-dev/api-service
```

---

## Troubleshooting

### 1. CI 빌드 실패

**확인**:
```bash
# GitHub Actions 로그 확인
# https://github.com/YOUR_ORG/agent-t/actions
```

**원인**:
- 테스트 실패 → 로컬에서 테스트 재실행
- Docker 빌드 실패 → Dockerfile 검증
- ECR 인증 실패 → AWS credentials 확인

### 2. Argo CD Sync 실패

**확인**:
```bash
argocd app get api-service
kubectl describe application api-service -n argocd
```

**원인**:
- Helm Chart 오류 → `helm template` 로컬 검증
- IRSA 권한 부족 → ServiceAccount annotation 확인
- Image pull 실패 → ECR 이미지 존재 여부 확인

### 3. Terraform Apply 실패

**확인**:
```bash
# GitHub Actions 로그 확인
# Terraform plan 결과 확인
```

**원인**:
- AWS 리소스 제한 초과
- IAM 권한 부족
- State lock 충돌

---

## Best Practices

1. **Git을 Single Source of Truth로 사용**
   - 클러스터에서 직접 수정 금지
   - 모든 변경은 Git PR/MR을 통해 진행

2. **작은 단위로 자주 배포**
   - 대규모 변경보다 작은 변경을 자주 배포
   - 롤백이 쉬움

3. **환경별 분리**
   - dev: 자동 배포, 빠른 피드백
   - prod: 수동 승인, 안전성 우선

4. **이미지 태그 명시**
   - `latest` 태그 사용 금지
   - 항상 명시적 SHA 태그 사용

5. **모니터링 및 알림**
   - Slack으로 배포 알림 받기
   - 실패 시 즉시 대응

6. **문서화**
   - 배포 절차, 롤백 방법 문서화
   - Runbook 작성

---

## 참고 문서

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Argo CD 문서](https://argo-cd.readthedocs.io/)
- [플랫폼 컴포넌트](./platform-components.md)
- [EKS 관리](./eks.md)
