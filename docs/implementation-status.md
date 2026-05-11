# Agent T 구현 상태 및 Bootstrap 체크리스트

## 현재 상태 (2026-05-11)

### ✅ 완료된 항목

#### 인프라 (Terraform)
- [x] VPC (Subnets, NAT Gateway, Route Tables)
- [x] EKS Cluster + Node Groups
- [x] RDS PostgreSQL
- [x] ElastiCache Redis
- [x] S3 Buckets (artifact, rag_source, reports, model_data)
- [x] ECR Repositories (7개 서비스)
- [x] Secrets Manager (db_credentials, redis_auth, app_secrets, bedrock_config)
- [x] VPC Endpoints (S3, ECR, Secrets Manager, KMS, CloudWatch)
- [x] IRSA (IAM Roles for Service Accounts)
- [x] ALB Controller IAM Policy + Role

#### 플랫폼
- [x] AWS Load Balancer Controller 설치
- [x] Argo CD 설치
- [x] Argo CD Applications 등록 (6개 서비스)
- [x] Terraform S3 Backend (State 관리)

#### 문서
- [x] README.md
- [x] QUICKSTART.md (로컬 Docker Compose)
- [x] DEPLOYMENT.md (AWS 배포)
- [x] SECURITY.md
- [x] GITHUB_STRATEGY.md
- [x] docs/troubleshooting.md

---

## ❌ 미구현 항목 (Bootstrap 완성을 위해 필요)

### 1. Terraform 모듈

#### Bedrock 모듈 (modules/bedrock)
**현재 상태**: 빈 파일 ("구현은 4단계에서 추가")

**필요한 내용**:
```hcl
# IAM Policy for Bedrock Access
resource "aws_iam_policy" "bedrock_invoke" {
  name = "${var.project_name}-${var.env}-bedrock-invoke"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels"
        ]
        Resource = [
          "arn:aws:bedrock:${var.region}::foundation-model/*"
        ]
      }
    ]
  })
}

output "bedrock_policy_arn" {
  value = aws_iam_policy.bedrock_invoke.arn
}
```

**용도**:
- Agent Service Pod가 Bedrock Claude 모델 호출
- IRSA를 통해 Pod에 권한 부여

**Bedrock 모델 활성화 (수동, 1회)**:
```bash
# AWS Console → Bedrock → Model access → Manage model access
# Claude 3.5 Sonnet, Claude 3 Opus 등 활성화
```

#### Argo CD 모듈 (modules/argocd)
**현재 상태**: 빈 파일

**이미 Helm으로 설치됨**: `install-platform.sh`에서 Helm Chart 사용
**모듈 필요 없음** (Helm으로 충분)

---

### 2. 애플리케이션 배포

#### Kubernetes Manifests
**현재 상태**: Argo CD Applications만 등록됨, 실제 Deployment/Service/Ingress 없음

**필요한 파일 구조**:
```
infra/k8s/
├── base/
│   ├── namespace.yaml
│   ├── secrets.yaml (참조만, 값은 External Secrets)
│   └── configmap.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   ├── frontend/
    │   │   ├── deployment.yaml
    │   │   ├── service.yaml
    │   │   └── ingress.yaml
    │   ├── api-service/
    │   ├── agent-service/
    │   ├── simulation-service/
    │   ├── analysis-service/
    │   └── report-service/
    └── prod/
```

**또는 Helm Charts**:
```
infra/helm/services/
├── frontend/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
├── api-service/
├── agent-service/
... (각 서비스)
```

#### External Secrets Operator (선택)
**목적**: Secrets Manager 값을 Kubernetes Secret으로 자동 동기화

**현재 상태**: 미설치

**필요 시 설치**:
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

---

### 3. 서비스별 구현 상태

#### Frontend
- [x] Docker Compose로 로컬 테스트 완료
- [x] ECR Repository 생성됨
- [ ] **Kubernetes Deployment/Service/Ingress**
- [ ] **이미지 빌드 및 ECR 푸시 (CI)**
- [ ] **Argo CD로 자동 배포**

#### API Service (Pipeline Service)
- [x] FastAPI 구현 완료
- [x] Docker Compose 테스트 완료
- [ ] Kubernetes Manifests
- [ ] 환경 변수 설정 (DB, Redis, S3 연결)

#### Agent Service
- [x] 기본 구조 완료
- [ ] **Bedrock 통합** (Claude 모델 호출)
- [ ] LLM Gateway 구현
- [ ] Kubernetes Manifests

#### Simulation Service
- [x] SUMO 통합 완료 (Placeholder 모드)
- [ ] OSM 실제 다운로드 구현
- [ ] Kubernetes Manifests

#### Analysis Service
- [x] 기본 구조 완료
- [ ] Kubernetes Manifests

#### Report Service
- [x] 기본 구조 완료
- [ ] Kubernetes Manifests

---

### 4. CI/CD

#### GitHub Actions Workflows
**현재 상태**: 미구성

**필요한 Workflows**:
```
.github/workflows/
├── build-and-push.yaml          # 이미지 빌드 및 ECR 푸시
├── deploy-dev.yaml              # dev 환경 배포
├── deploy-prod.yaml             # prod 환경 배포
└── terraform-plan.yaml          # Terraform PR 검증
```

**예시: build-and-push.yaml**:
```yaml
name: Build and Push to ECR

on:
  push:
    branches: [main, develop]
    paths:
      - 'apps/**'
      - 'libs/**'

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [frontend, api-service, agent-service, simulation-service, analysis-service, report-service]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-role
          aws-region: ap-northeast-2
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password --region ap-northeast-2 | \
          docker login --username AWS --password-stdin \
          ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-northeast-2.amazonaws.com
      
      - name: Build and push
        run: |
          cd apps/${{ matrix.service }}
          docker build -t agent-t-dev/${{ matrix.service }}:${{ github.sha }} .
          docker tag agent-t-dev/${{ matrix.service }}:${{ github.sha }} \
            ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/${{ matrix.service }}:${{ github.sha }}
          docker push ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/${{ matrix.service }}:${{ github.sha }}
```

#### Argo CD Image Updater (선택)
**목적**: ECR에 새 이미지 푸시 시 자동 배포

---

### 5. 모니터링 및 로깅

#### 미구현
- [ ] Prometheus + Grafana
- [ ] Loki (로그 수집)
- [ ] Alertmanager (알림)
- [ ] CloudWatch Container Insights

---

### 6. Secret 초기값 설정

#### Secrets Manager에 값 주입 (수동, 1회)
```bash
# DB 자격 증명 (Terraform random_password로 자동 생성됨 - 확인만)
aws secretsmanager get-secret-value \
  --secret-id agent-t-dev-db-credentials \
  --query SecretString --output text | jq

# Redis AUTH Token (Terraform random_password로 자동 생성됨)
aws secretsmanager get-secret-value \
  --secret-id agent-t-dev-redis-auth \
  --query SecretString --output text

# Bedrock 설정 (빈 값, 필요 시 수동 추가)
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-bedrock-config \
  --secret-string '{
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "temperature": 0.7,
    "max_tokens": 4096
  }'

# 애플리케이션 Secret (외부 API Key 등)
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-app-secrets \
  --secret-string '{
    "openai_api_key": "sk-...",
    "sumo_api_key": "..."
  }'
```

---

## Bootstrap 완성을 위한 우선순위

### P0 (필수, Bootstrap 스크립트 완성)
1. **Bedrock 모듈 구현** → Terraform
2. **IRSA에 Bedrock Policy 연결** → Terraform
3. **Frontend Ingress 생성** → Kubernetes Manifest 또는 Helm

### P1 (서비스 정상 동작)
4. **각 서비스 Kubernetes Manifests** → Kustomize 또는 Helm
5. **환경 변수 주입** (DB, Redis, S3 연결 정보)
6. **이미지 빌드 및 ECR 푸시** → GitHub Actions
7. **Argo CD 자동 배포 설정**

### P2 (Production Ready)
8. **Monitoring** (Prometheus, Grafana)
9. **Logging** (Loki, CloudWatch)
10. **Alerting** (Alertmanager, SNS)
11. **Backup** (RDS 스냅샷, S3 버저닝)

---

## 새 환경에서 Bootstrap 실행 시 필요한 사전 작업

### 완전 자동화 가능 (스크립트에 포함)
- [x] AWS CLI 설치 확인
- [x] kubectl, helm, terraform 설치 확인
- [x] AWS 인증 확인
- [x] Terraform Backend (S3 + DynamoDB) 생성
- [x] Terraform init + apply
- [x] EKS kubeconfig 동기화
- [x] ALB Controller + Argo CD 설치

### 수동 작업 필요 (1회, 사람 판단 필요)
- [ ] **Bedrock 모델 액세스 활성화** (AWS Console)
- [ ] **도메인 NS 레코드 설정** (다른 계정)
- [ ] **Secrets Manager에 외부 API Key 주입** (OpenAI 등)

---

## 다음 작업

### 즉시 (현재 세션)
1. Bedrock 모듈 구현
2. IRSA에 Bedrock Policy 추가
3. Frontend Ingress 생성 (단순 HTTP, ALB 주소 확보)

### 이후 (별도 세션)
4. 전체 서비스 Kubernetes Manifests 작성
5. CI/CD Pipeline 구현
6. Monitoring 설정
