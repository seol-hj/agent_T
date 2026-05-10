# AWS 배포 가이드

로컬 테스트 완료 후 AWS 프로덕션 환경으로 배포하는 전체 가이드

---

## ✅ 현재 상태 (v0.4.0)

**로컬 개발 환경 완료**:
- ✅ Docker Compose로 6개 서비스 실행 (pipeline, agent, simulation, analysis, report, frontend)
- ✅ PostgreSQL DB 연동 (파이프라인 실행 상태 추적)
- ✅ MockLLMProvider로 LLM 동작 테스트
- ✅ LocalStorageGateway로 파일 저장 테스트
- ✅ SUMO 실제 통합 (placeholder fallback 지원)
- ✅ Next.js 14 프론트엔드 (실시간 진행률 모니터링)
- ✅ E2E 파이프라인 정상 동작

---

## 🎯 AWS 배포 전체 프로세스

### 배포 아키텍처 개요

```
GitHub Repo
    ↓
 CI: GitHub Actions
    ↓ (Docker Build + ECR Push)
 ECR (Container Registry)
    ↓
 CD: Argo CD (GitOps)
    ↓
 EKS (Kubernetes)
    ├── Agent Service
    ├── Simulation Service  
    ├── Analysis Service
    ├── Report Service
    ├── Pipeline Service
    └── Frontend (Next.js)
    ↓
 ALB (Application Load Balancer)
    ↓
 Users
```

**AWS 리소스**:
- **Compute**: EKS (Managed Kubernetes)
- **Database**: RDS PostgreSQL 15 (Multi-AZ)
- **Cache**: ElastiCache Redis 7
- **Storage**: S3 (시뮬레이션 결과, 네트워크 파일)
- **AI**: Amazon Bedrock (Claude 3.5 Sonnet)
- **Networking**: VPC, ALB, NAT Gateway, VPC Endpoints
- **CI/CD**: GitHub Actions + Argo CD
- **Monitoring**: CloudWatch + Prometheus + Grafana

---

### Phase 1: AWS 인프라 구축 (Terraform)

**목표**: VPC, EKS, RDS, S3, ECR 등 전체 AWS 리소스 생성

#### 1.1 사전 준비

```bash
# 필수 도구 설치 확인
./scripts/check-env.sh
```

**필수 도구**:
- AWS CLI 2.x
- Terraform 1.5+
- kubectl 1.28+
- Helm 3.x
- jq

#### 1.2 AWS 인증 설정

```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: ap-northeast-2
# Default output format: json

# 인증 확인
aws sts get-caller-identity
```

#### 1.3 전체 환경 자동 구축

```bash
# Checkpoint 지원 - 중단 시 이어서 진행 가능
./scripts/bootstrap-dev.sh
```

**생성 리소스**:
- VPC + 3-tier Subnets (Public/Private/Data)
- NAT Gateway (3개 AZ)
- EKS Cluster 1.30
- EKS Managed Node Groups (2-5 nodes)
- RDS PostgreSQL 15
- ElastiCache Redis 7
- S3 Buckets (storage, artifacts, logs)
- ECR Repositories (5개 서비스)
- VPC Endpoints (S3, ECR, Bedrock, Secrets Manager, STS, CloudWatch)
- AWS Load Balancer Controller
- Argo CD

**예상 비용**: ~$150-200/월 (dev 환경)

**소요 시간**: 20-30분

**중단 시**:
- Checkpoint가 자동 저장됨
- 다시 `./scripts/bootstrap-dev.sh` 실행하면 이어서 진행

#### 1.4 구축 확인

```bash
# EKS 클러스터 확인
kubectl get nodes

# ALB Controller 확인
kubectl get pods -n kube-system | grep aws-load-balancer

# Argo CD 확인
kubectl get pods -n argocd

# Argo CD 비밀번호 조회
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

---

### Phase 2: 서비스 배포 (10-15분)

**목표**: Docker 이미지 빌드 + ECR Push + Kubernetes 배포

#### 2.1 Docker 이미지 빌드 & ECR Push

```bash
# 각 서비스별로 빌드 & Push
cd apps/agent-service
docker build -t agent-service:latest .

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 태그 & Push
docker tag agent-service:latest \
  <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t/agent-service:v0.4.0

docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t/agent-service:v0.4.0
```

**반복 대상**:
- pipeline (Port 8000)
- agent-service (Port 8001)
- simulation-service (Port 8005)
- analysis-service (Port 8006)
- report-service (Port 8007)
- frontend (Port 3000, Next.js)

#### 2.2 Helm 배포

```bash
# 각 서비스별로 Helm 설치
cd infra/helm/services/agent-service

# values.yaml 수정 (ECR 이미지 URL)
vim values.yaml

# Helm 설치
helm install agent-service . \
  --namespace agent-t \
  --create-namespace \
  --values values.yaml
```

#### 2.3 Argo CD로 자동 배포 (권장)

```bash
# Argo CD Applications 등록
./scripts/register-argocd-apps.sh

# Argo CD UI 접속
kubectl port-forward svc/argocd-server -n argocd 8080:443

# https://localhost:8080 접속
# Username: admin
# Password: (1.4에서 조회한 비밀번호)
```

Argo CD에서 자동으로 Git 변경사항을 감지하고 배포합니다.

---

### Phase 3: AWS 리소스 연동

**목표**: RDS PostgreSQL, S3, Bedrock 연동

#### 3.1 PostgreSQL (RDS) 연동

```bash
# Terraform으로 생성된 RDS 엔드포인트 조회
cd infra/terraform/envs/dev
terraform output rds_endpoint

# Kubernetes Secret 생성
kubectl create secret generic postgres-secret \
  --from-literal=username=agent_t \
  --from-literal=password=<terraform-output-password> \
  --from-literal=host=<rds-endpoint> \
  --from-literal=database=agent_t_db \
  -n agent-t

# Pipeline Service values.yaml 업데이트
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: postgres-secret
        key: connection-string
```

**RDS 설정** (Terraform 자동 생성):
- Engine: PostgreSQL 15
- Instance: db.t4g.micro (Dev) / db.t4g.large (Prod)
- Multi-AZ: Enabled (Prod)
- Backup: 7일 보관
- VPC: Private Subnet

#### 3.2 S3 Storage 연동

```bash
# S3 버킷 조회
terraform output s3_storage_bucket

# 환경 변수 업데이트 (모든 서비스)
env:
  - name: STORAGE_PROVIDER
    value: "s3"
  - name: STORAGE_BUCKET
    value: "agent-t-storage-dev"
  - name: AWS_REGION
    value: "ap-northeast-2"
```

**S3 버킷 구조**:
```
agent-t-storage-dev/
├── scenarios/          # 시나리오 명세
│   └── exp-{id}/
├── networks/           # SUMO 네트워크 파일
│   └── exp-{id}/
├── demands/            # 교통 수요 파일
│   └── exp-{id}/
├── simulations/        # 시뮬레이션 결과
│   └── exp-{id}/
│       ├── tripinfo.xml
│       ├── summary.xml
│       └── fcd.xml
├── analysis/           # 분석 결과
│   └── exp-{id}/
└── reports/            # 최종 리포트
    └── exp-{id}/
```

#### 3.3 Bedrock (LLM) 연동

```bash
# Agent Service와 Report Service에만 적용
env:
  - name: LLM_PROVIDER
    value: "bedrock"
  - name: AWS_REGION
    value: "us-east-1"  # Bedrock 지원 리전
  - name: LLM_MODEL_ID
    value: "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

**Bedrock 지원 리전**:
- us-east-1 (N. Virginia) - 권장
- us-west-2 (Oregon)
- eu-west-1 (Ireland)
- ap-northeast-1 (Tokyo)

**모델 선택**:
- `anthropic.claude-3-5-sonnet-20241022-v2:0` - 가장 최신, 성능 우수
- `anthropic.claude-3-sonnet-20240229-v1:0` - 안정적
- `anthropic.claude-3-haiku-20240307-v1:0` - 저렴, 빠름

#### 3.4 IRSA (IAM Roles for Service Accounts)

```yaml
# 각 서비스의 ServiceAccount에 IAM Role 연결
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pipeline-service
  namespace: agent-t
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<account-id>:role/agent-t-pipeline-role

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agent-service
  namespace: agent-t
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<account-id>:role/agent-t-agent-role
```

**IAM 권한** (Terraform 자동 생성):

| Service | S3 | RDS | Bedrock | ECR |
|---------|----|----|---------|-----|
| pipeline | R/W | R/W | - | R |
| agent-service | R/W | - | Invoke | R |
| simulation-service | R/W | - | - | R |
| analysis-service | R/W | - | - | R |
| report-service | R/W | - | Invoke | R |
| frontend | - | - | - | R |

---

### Phase 4: 테스트 (5분)

#### 4.1 서비스 상태 확인

```bash
# Pod 상태
kubectl get pods -n agent-t

# Service 상태
kubectl get svc -n agent-t

# Ingress 상태
kubectl get ingress -n agent-t
```

#### 4.2 ALB URL 조회

```bash
# ALB DNS 조회
kubectl get ingress -n agent-t -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}'
```

#### 4.3 E2E 테스트

```bash
ALB_URL=$(kubectl get ingress -n agent-t -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')

curl -X POST http://${ALB_URL}/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "prod-test-001",
    "user_request": "서울 강남역 일대 교통 시뮬레이션",
    "dry_run": false
  }' | jq
```

**예상 결과**: Bedrock LLM을 사용한 실제 AI 응답 + S3 저장

---

## 📊 환경별 차이점

### 로컬 (Docker Compose)

| 항목 | 설정 |
|------|------|
| LLM | MockLLMProvider (하드코딩 응답) |
| Storage | LocalStorageGateway (`/data` 볼륨) |
| Database | PostgreSQL 15 (Docker 컨테이너) |
| Frontend | Next.js 14 (localhost:3000) |
| 비용 | 무료 |
| 확장성 | 제한적 (단일 머신) |
| 용도 | 개발/테스트 |

### AWS Dev 환경

| 항목 | 설정 |
|------|------|
| LLM | Bedrock (Claude 3.5 Sonnet) |
| Storage | S3 (`agent-t-storage-dev`) |
| Database | RDS PostgreSQL 15 (db.t4g.micro) + ElastiCache Redis |
| Frontend | Next.js 14 (ALB를 통해 배포) |
| Ingress | ALB (AWS Load Balancer Controller) |
| 비용 | ~$150-200/월 |
| 확장성 | Auto Scaling (2-5 nodes) |
| 용도 | 스테이징/통합 테스트 |

### AWS Prod 환경 (향후)

| 항목 | 설정 |
|------|------|
| LLM | Bedrock (Claude 3.5 Sonnet 또는 Opus) |
| Storage | S3 (Multi-region replication) |
| Database | RDS Multi-AZ (db.t4g.large+) + Redis Cluster |
| Frontend | CloudFront + S3 (정적 배포) 또는 EKS |
| Ingress | ALB + CloudFront + WAF |
| 비용 | ~$500-800/월 |
| 확장성 | Auto Scaling (5-20 nodes) |
| 용도 | 프로덕션 |

---

## 🔄 CI/CD 파이프라인

### 전체 흐름

```
코드 변경 (Git Push)
    ↓
GitHub Actions (CI)
    ├── 테스트 실행
    ├── Docker 이미지 빌드
    ├── ECR Push (Git SHA 태그)
    └── Helm values 업데이트 + Git Push
    ↓
Argo CD (CD) - 자동 감지
    ├── Git Repo Sync
    ├── Helm Chart 렌더링
    ├── Kubernetes Apply
    └── Health Check
    ↓
EKS에 배포 완료
```

### GitHub Actions (CI)

**Trigger**: Push to `main` branch

**Workflow Example** (`.github/workflows/ci-pipeline.yml`):
```yaml
name: CI - Pipeline Service

on:
  push:
    branches: [main]
    paths:
      - 'apps/pipeline/**'
      - 'libs/**'

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2

      - name: Login to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}

      - name: Build and Push
        run: |
          IMAGE_TAG=${GITHUB_SHA::7}
          docker build -t pipeline:$IMAGE_TAG -f apps/pipeline/Dockerfile .
          docker tag pipeline:$IMAGE_TAG ${{ secrets.ECR_REGISTRY }}/agent-t/pipeline:$IMAGE_TAG
          docker push ${{ secrets.ECR_REGISTRY }}/agent-t/pipeline:$IMAGE_TAG

      - name: Update Helm values
        run: |
          IMAGE_TAG=${GITHUB_SHA::7}
          sed -i "s/tag: .*/tag: $IMAGE_TAG/" infra/helm/services/pipeline/values.yaml
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add infra/helm/services/pipeline/values.yaml
          git commit -m "Update pipeline image to $IMAGE_TAG"
          git push
```

**필요한 GitHub Secrets**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `ECR_REGISTRY` (예: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com)

### Argo CD (CD)

**자동 배포 설정** (`infra/argocd/applications/dev/pipeline.yaml`):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: pipeline
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<your-org>/agent-t.git
    targetRevision: main
    path: infra/helm/services/pipeline
  destination:
    server: https://kubernetes.default.svc
    namespace: agent-t
  syncPolicy:
    automated:
      prune: true      # 삭제된 리소스 자동 제거
      selfHeal: true   # 수동 변경 시 자동 복구
    syncOptions:
      - CreateNamespace=true
```

**Argo CD 접속**:
```bash
# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 비밀번호 조회
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# https://localhost:8080 접속
# Username: admin
# Password: (위에서 조회한 값)
```

### 배포 프로세스 타임라인

| 단계 | 소요 시간 | 설명 |
|------|----------|------|
| 1. Git Push | 0초 | 코드 변경 커밋 |
| 2. GitHub Actions 트리거 | ~10초 | Workflow 시작 |
| 3. Docker 빌드 + ECR Push | ~3-5분 | 멀티 서비스의 경우 병렬 실행 |
| 4. Helm values 업데이트 | ~10초 | Git commit + push |
| 5. Argo CD 감지 | ~1-3분 | Git polling interval |
| 6. Kubernetes 배포 | ~1-2분 | Pod 재시작 |
| **전체** | **~5-10분** | 코드 변경부터 배포 완료까지 |

### 수동 배포 (필요시)

```bash
# Argo CD CLI로 수동 Sync
argocd app sync pipeline

# 또는 UI에서 "SYNC" 버튼 클릭
```

---

## 🚨 중요 사항

### 비용 관리

```bash
# 사용하지 않을 때는 반드시 삭제
cd infra/terraform/envs/dev
terraform destroy

# 주의: RDS/Redis는 snapshot 생성 후 삭제
```

**예상 비용** (Dev 환경):
- EKS: ~$75/월 (Control Plane $73 + Node Groups)
- RDS: ~$30/월 (db.t4g.micro)
- ElastiCache: ~$15/월 (cache.t4g.micro)
- NAT Gateway: ~$35/월 (3개)
- S3/ECR: ~$5/월

**절약 팁**:
- NAT Gateway 1개만 사용 (Multi-AZ 포기)
- RDS/Redis Auto Pause (활용도 낮을 때)
- Spot Instances 사용 (Node Groups)

### 보안

**절대 Git 커밋 금지**:
- AWS Access Key / Secret Key
- RDS 비밀번호
- `*.pem`, `*.key`, `.env`

**사용**:
- AWS Secrets Manager (모든 비밀)
- IRSA (Pod별 IAM 역할)
- VPC Endpoint (인터넷 경유 없음)

### 재현성

전체 환경 삭제 후 재구축:

```bash
# 삭제
cd infra/terraform/envs/dev
terraform destroy

# 재구축 (20-30분)
./scripts/bootstrap-dev.sh
```

---

## 📚 참고 문서

| 문서 | 설명 |
|------|------|
| [docs/deployment.md](./docs/deployment.md) | AWS 배포 상세 가이드 |
| [docs/rebuild-environment.md](./docs/rebuild-environment.md) | 환경 재구축 가이드 (627줄) |
| [docs/observability.md](./docs/observability.md) | 관측성 아키텍처 |
| [CLAUDE.md](./CLAUDE.md) | 프로젝트 설계 원칙 |

---

## ❓ FAQ

### Q1. Docker Compose와 AWS 배포의 관계는?

**A**: 완전히 독립적입니다.
- Docker Compose: 로컬 개발/테스트용
- AWS: 프로덕션 환경
- 서로 영향을 주지 않습니다.

### Q2. Terraform 없이 수동으로 배포 가능한가?

**A**: 가능하지만 권장하지 않습니다.
- Terraform: 재현 가능, 코드 리뷰 가능, 변경 추적
- 수동: 휴먼 에러, 재현 불가, 변경 추적 어려움

### Q3. Bedrock이 없으면 AWS 배포 불가능한가?

**A**: 아니요, LocalLLMProvider로 대체 가능합니다.
- Ollama 등 Self-hosted LLM 사용
- LLM_PROVIDER=local 설정
- 단, 성능/품질은 Bedrock 대비 낮음

### Q4. SUMO가 없으면 시뮬레이션 불가능한가?

**A**: 아니요, Placeholder 모드로 동작합니다.
- SUMO 미설치 시 자동 Fallback
- 테스트용 더미 데이터 생성
- 실제 프로덕션에서는 SUMO 설치 권장

### Q5. 비용이 너무 높은데 줄일 수 있나?

**A**: 가능합니다.
- NAT Gateway 1개만 사용 (~$25 절약)
- Spot Instances 사용 (~30% 절약)
- RDS/Redis 작은 인스턴스 (~$20 절약)
- 사용하지 않을 때 terraform destroy

---

## ✅ 체크리스트

### ✅ 로컬 개발 완료
- [x] Docker Compose 실행 (6개 서비스)
- [x] PostgreSQL DB 연동
- [x] Next.js 프론트엔드 구현
- [x] 실시간 진행률 모니터링 (2초 폴링)
- [x] E2E 파이프라인 정상 동작
- [x] SUMO placeholder fallback 구현

### 📋 AWS 배포 준비
- [ ] AWS CLI 설치 및 인증 (`aws configure`)
- [ ] Terraform 1.5+ 설치
- [ ] kubectl 1.28+ 설치
- [ ] Helm 3.x 설치
- [ ] AWS 계정 준비 (Admin 권한 또는 적절한 IAM 정책)
- [ ] GitHub Secrets 등록 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, ECR_REGISTRY)

### 🏗️ AWS 인프라 구축 (Phase 1)
- [ ] `./scripts/bootstrap-dev.sh` 실행 (20-30분)
- [ ] EKS 클러스터 접속 확인 (`kubectl get nodes`)
- [ ] ALB Controller 설치 확인 (`kubectl get pods -n kube-system`)
- [ ] Argo CD 설치 확인 (`kubectl get pods -n argocd`)
- [ ] RDS PostgreSQL 엔드포인트 조회 (`terraform output rds_endpoint`)
- [ ] S3 버킷 조회 (`terraform output s3_storage_bucket`)

### 🚀 서비스 배포 (Phase 2)
- [ ] Docker 이미지 빌드 (6개 서비스)
- [ ] ECR Push (GitHub Actions 또는 수동)
- [ ] Kubernetes Secret 생성 (PostgreSQL 연결 정보)
- [ ] Helm 배포 또는 Argo CD Application 등록
- [ ] Pod 정상 동작 확인 (`kubectl get pods -n agent-t`)
- [ ] Service 확인 (`kubectl get svc -n agent-t`)
- [ ] Ingress 확인 (`kubectl get ingress -n agent-t`)

### 🔗 AWS 리소스 연동 (Phase 3)
- [ ] RDS PostgreSQL 연동 (DATABASE_URL 환경변수)
- [ ] S3 버킷 연동 (STORAGE_PROVIDER=s3, STORAGE_BUCKET)
- [ ] Bedrock 환경 변수 설정 (LLM_PROVIDER=bedrock, us-east-1)
- [ ] IRSA 설정 확인 (ServiceAccount IAM Role)
- [ ] VPC Endpoint 동작 확인 (인터넷 경유 없이 S3/Bedrock 접근)

### 🧪 테스트 (Phase 4)
- [ ] ALB URL 조회 (`kubectl get ingress -n agent-t`)
- [ ] 프론트엔드 접속 (http://<alb-url>)
- [ ] 새 실험 생성
- [ ] 실시간 진행률 모니터링 확인
- [ ] Bedrock LLM 응답 확인 (실제 AI 응답)
- [ ] S3 저장 확인 (시뮬레이션 결과 파일)
- [ ] RDS 저장 확인 (실행 이력)

### 📊 모니터링 설정 (Optional)
- [ ] CloudWatch Logs 확인
- [ ] CloudWatch Container Insights 활성화
- [ ] Prometheus + Grafana 배포
- [ ] 알람 설정 (CloudWatch Alarms)

---

## 🚀 빠른 시작 (TL;DR)

```bash
# 1. AWS 인증
aws configure

# 2. 인프라 구축 (20-30분)
./scripts/bootstrap-dev.sh

# 3. Docker 이미지 빌드 & Push
./scripts/build-and-push-all.sh  # 향후 추가 예정

# 4. Argo CD로 배포
kubectl apply -f infra/argocd/applications/dev/

# 5. ALB URL 조회 및 접속
kubectl get ingress -n agent-t
```

---

**최종 업데이트**: 2026-05-10  
**버전**: 0.4.0  
**상태**: 로컬 테스트 완료, AWS 배포 준비 완료
