# 환경 구조 가이드

AI Agent T는 **3가지 환경**을 지원합니다: Local, Dev, Prod

---

## 환경별 개요

| 환경 | 목적 | 인프라 | 도메인 | LLM | Storage |
|---|---|---|---|---|---|
| **Local** | 개발/테스트 | Docker Compose | localhost | Mock | Local Filesystem |
| **Dev** | 개발 통합 | AWS EKS (dev) | agent-dev.seolphung.com | Bedrock (Claude) | S3 |
| **Prod** | 프로덕션 | AWS EKS (prod) | agent.seolphung.com | Bedrock (Claude) | S3 |

---

## 1. Local 환경 (로컬 개발)

### 목적
- 개발자 로컬 머신에서 전체 시스템 테스트
- AWS 비용 없이 빠른 개발/디버깅
- CI 없이 즉시 코드 변경 확인

### 인프라
- **Docker Compose** - 모든 서비스 컨테이너화
- **PostgreSQL** - 로컬 DB 컨테이너
- **Local Filesystem** - `/data` 볼륨 마운트
- **Mock LLM** - 하드코딩된 응답 (Bedrock 호출 없음)

### 파일 위치
```
docker-compose.yaml           # 전체 서비스 정의
apps/*/Dockerfile             # 각 서비스 이미지
libs/common/gateways/llm.py   # MockLLMProvider 사용
libs/common/gateways/storage.py # LocalStorageProvider 사용
```

### 설정 방법

**환경 변수** (`.env.local` 또는 docker-compose.yaml):
```bash
ENV=local
LLM_PROVIDER=mock           # MockLLMProvider 사용
STORAGE_PROVIDER=local      # LocalStorageProvider 사용
DB_HOST=postgres            # docker-compose service name
DB_PORT=5432
DB_NAME=agent_t
DB_USER=agent_t
DB_PASSWORD=agent_t_pass
STORAGE_PATH=/data          # 로컬 볼륨
```

### 실행 방법
```bash
# 1. 전체 시스템 시작
docker compose up --build

# 2. Frontend 접속
open http://localhost:3000

# 3. 개별 서비스 테스트
curl http://localhost:8000/health  # API Service
curl http://localhost:8001/health  # Agent Service (Mock LLM)
```

### 특징
- ✅ AWS 계정 불필요
- ✅ 빠른 빌드/재시작
- ✅ 로그 실시간 확인 (`docker compose logs -f`)
- ❌ Bedrock 실제 LLM 호출 불가
- ❌ S3 저장 불가
- ❌ Multi-node 테스트 불가

---

## 2. Dev 환경 (개발 통합)

### 목적
- 실제 AWS 환경에서 통합 테스트
- CI/CD 파이프라인 검증
- Bedrock 실제 LLM 호출 테스트
- 팀 공유 개발 환경

### 인프라
- **AWS EKS** - `agent-t-dev` 클러스터
- **RDS PostgreSQL** - Multi-AZ
- **ElastiCache Redis** - 단일 노드
- **S3** - 3개 버킷 (rag-source, artifact, reports)
- **Bedrock** - Claude 3.5 Sonnet
- **ALB** - internet-facing
- **Route53** - `agent-dev.seolphung.com`

### 파일 위치
```
infra/terraform/envs/dev/          # Terraform 설정
  ├── main.tf                      # 환경별 변수
  ├── terraform.tfvars             # Dev 전용 값
  └── backend.tf                   # S3 backend

infra/helm/services/*/values-dev.yaml  # Helm Dev 오버라이드
infra/argocd/applications/dev/         # Argo CD Dev Apps

.github/workflows/ci-*.yml         # CI에서 dev ECR로 푸시
```

### 설정 방법

**Terraform variables** (`infra/terraform/envs/dev/terraform.tfvars`):
```hcl
project_name = "agent-t"
environment  = "dev"
aws_region   = "ap-northeast-2"

# 작은 인스턴스
eks_node_instance_types = ["t3.medium"]
rds_instance_class      = "db.t3.micro"
redis_node_type         = "cache.t3.micro"

# 최소 리소스
eks_min_size = 2
eks_max_size = 4
rds_multi_az = false  # 비용 절감
```

**Helm values** (`infra/helm/services/*/values-dev.yaml`):
```yaml
replicaCount: 1  # 최소 replica

image:
  repository: 190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/frontend
  tag: "sha-xxxxxxx"  # CI에서 자동 업데이트

resources:
  requests:
    cpu: 50m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi

config:
  LOG_LEVEL: "debug"  # 상세 로그
  DB_HOST: "agent-t-dev-postgres.xxxxx.rds.amazonaws.com"
  REDIS_HOST: "agent-t-dev-redis.xxxxx.cache.amazonaws.com"

ingress:
  enabled: true
  hosts:
    - host: agent-dev.seolphung.com
```

### 환경 변수 (자동 주입)
```bash
ENV=dev
LLM_PROVIDER=bedrock        # 실제 Bedrock 호출
STORAGE_PROVIDER=s3         # 실제 S3 저장
AWS_REGION=ap-northeast-2
AWS_ROLE_ARN=arn:aws:iam::190484841865:role/agent-t-dev-xxx-irsa  # IRSA
```

### 배포 방법
```bash
# 1. Terraform 인프라 구축
cd infra/terraform/envs/dev
terraform apply

# 2. EKS 접속
aws eks update-kubeconfig --name agent-t-dev --region ap-northeast-2

# 3. Argo CD로 서비스 배포
kubectl apply -f infra/argocd/applications/dev/

# 4. 접속 (HTTPS)
open https://agent-dev.seolphung.com
```

### CI/CD 동작
```
Code Push (main branch)
  ↓
GitHub Actions
  ↓
Docker Build
  ↓
ECR Push (agent-t-dev/*)
  ↓
Update gitops/dev branch
  ↓
Argo CD Auto Sync (3분마다)
  ↓
EKS Pod 재시작
```

### 특징
- ✅ 실제 Bedrock LLM 호출
- ✅ 실제 S3 저장
- ✅ 팀 공유 가능
- ✅ CI/CD 자동 배포
- ⚠️ AWS 비용 발생 (낮음)
- ⚠️ 빌드 시간 필요 (2~5분)

---

## 3. Prod 환경 (프로덕션)

### 목적
- 실제 서비스 운영
- 고가용성 (HA)
- 프로덕션 워크로드

### 인프라
- **AWS EKS** - `agent-t-prod` 클러스터
- **RDS PostgreSQL** - **Multi-AZ** (HA)
- **ElastiCache Redis** - **Cluster mode** (HA)
- **S3** - 3개 버킷 (버전 관리 활성화)
- **Bedrock** - Claude 3.5 Sonnet
- **ALB** - internet-facing + WAF
- **Route53** - `agent.seolphung.com`
- **CloudWatch** - 알람 + 대시보드

### 파일 위치
```
infra/terraform/envs/prod/          # Terraform 설정
  ├── main.tf
  ├── terraform.tfvars             # Prod 전용 값
  └── backend.tf                   # S3 backend (별도 버킷)

infra/helm/services/*/values-prod.yaml  # Helm Prod 오버라이드
infra/argocd/applications/prod/         # Argo CD Prod Apps
```

### 설정 방법

**Terraform variables** (`infra/terraform/envs/prod/terraform.tfvars`):
```hcl
project_name = "agent-t"
environment  = "prod"
aws_region   = "ap-northeast-2"

# 프로덕션 인스턴스
eks_node_instance_types = ["t3.large", "t3.xlarge"]
rds_instance_class      = "db.r6g.large"
redis_node_type         = "cache.r6g.large"

# 고가용성
eks_min_size = 4
eks_max_size = 20
rds_multi_az = true  # HA 필수
redis_num_cache_clusters = 2  # Cluster mode

# 백업
rds_backup_retention_period = 30
s3_versioning_enabled       = true
```

**Helm values** (`infra/helm/services/*/values-prod.yaml`):
```yaml
replicaCount: 3  # 최소 3개 replica (HA)

image:
  repository: 190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-prod/frontend
  tag: "v1.0.0"  # Semantic versioning

resources:
  requests:
    cpu: 200m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 2Gi

config:
  LOG_LEVEL: "info"  # 최소 로그
  DB_HOST: "agent-t-prod-postgres.xxxxx.rds.amazonaws.com"
  REDIS_HOST: "agent-t-prod-redis.xxxxx.cache.amazonaws.com"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  hosts:
    - host: agent.seolphung.com
  annotations:
    alb.ingress.kubernetes.io/wafv2-acl-arn: "arn:aws:wafv2:..."  # WAF 보호
```

### 배포 방법 (승인 필요)
```bash
# 1. Terraform 인프라 구축
cd infra/terraform/envs/prod
terraform plan  # 검토 필수
terraform apply  # 승인 후 실행

# 2. EKS 접속
aws eks update-kubeconfig --name agent-t-prod --region ap-northeast-2

# 3. Argo CD로 서비스 배포 (Manual Sync)
kubectl apply -f infra/argocd/applications/prod/
# Argo CD UI에서 수동 Sync (Auto Sync 금지)

# 4. 접속 (HTTPS only)
open https://agent.seolphung.com
```

### CI/CD 동작 (수동 승인)
```
Code Push (release branch)
  ↓
GitHub Actions (Manual Approval)
  ↓
Docker Build
  ↓
ECR Push (agent-t-prod/*)
  ↓
Create Git Tag (v1.0.0)
  ↓
Update gitops/prod branch (Manual PR)
  ↓
Argo CD Manual Sync
  ↓
Blue-Green Deployment
```

### 특징
- ✅ 고가용성 (Multi-AZ)
- ✅ 자동 스케일링
- ✅ WAF 보호
- ✅ 30일 백업
- ✅ CloudWatch 알람
- ⚠️ AWS 비용 높음
- ⚠️ 배포 승인 필요

---

## 환경 전환 방법

### 1. 로컬 → Dev
```bash
# 코드 변경 후 main에 push
git push origin main

# GitHub Actions가 자동으로:
# 1. Docker build
# 2. ECR push (dev)
# 3. gitops/dev 업데이트
# 4. Argo CD auto sync (3분 내)
```

### 2. Dev → Prod
```bash
# 1. Git tag 생성 (semantic versioning)
git tag v1.0.0
git push origin v1.0.0

# 2. Manual approval in GitHub Actions
# 3. ECR push (prod)

# 4. PR to gitops/prod
git checkout gitops/prod
# Update values-prod.yaml with new tag
git commit -m "chore: release v1.0.0"
git push origin gitops/prod

# 5. Argo CD에서 Manual Sync
```

### 3. Prod → Rollback
```bash
# 1. 이전 tag로 복구
git checkout gitops/prod
# Update values-prod.yaml to previous tag
git commit -m "chore: rollback to v0.9.9"
git push origin gitops/prod

# 2. Argo CD에서 Manual Sync
```

---

## 환경별 차이 요약

| 항목 | Local | Dev | Prod |
|---|---|---|---|
| **인프라** | Docker Compose | AWS EKS (dev) | AWS EKS (prod) |
| **LLM** | Mock | Bedrock | Bedrock |
| **Storage** | Local FS | S3 | S3 + Versioning |
| **DB** | Postgres 컨테이너 | RDS Single-AZ | RDS Multi-AZ |
| **Redis** | 없음 | ElastiCache 단일 | ElastiCache Cluster |
| **도메인** | localhost | agent-dev.seolphung.com | agent.seolphung.com |
| **HTTPS** | 없음 | ACM | ACM + WAF |
| **Replica** | 1 | 1 | 3+ |
| **Auto Scale** | 없음 | 없음 | HPA 활성화 |
| **배포** | 수동 | Auto (CI/CD) | Manual Approval |
| **로그 레벨** | debug | debug | info |
| **비용** | 무료 | ~$100/월 | ~$500/월 |
| **목적** | 개발/디버깅 | 통합 테스트 | 프로덕션 |

---

## 환경 변수 주입 방식

### Local (Docker Compose)
```yaml
services:
  frontend:
    environment:
      - ENV=local
      - LLM_PROVIDER=mock
      - STORAGE_PROVIDER=local
```

### Dev/Prod (Kubernetes)
```yaml
# ConfigMap으로 주입
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend
data:
  ENV: "dev"
  LLM_PROVIDER: "bedrock"
  STORAGE_PROVIDER: "s3"

# IRSA로 AWS 인증
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::xxx:role/agent-t-dev-frontend-irsa"
```

---

## 관련 문서

- `docker-compose.yaml` - Local 환경 정의
- `infra/terraform/envs/dev/` - Dev 환경 Terraform
- `infra/terraform/envs/prod/` - Prod 환경 Terraform
- `infra/helm/services/*/values-dev.yaml` - Dev Helm values
- `infra/helm/services/*/values-prod.yaml` - Prod Helm values (작성 필요)
- `docs/DEPLOYMENT.md` - AWS 배포 가이드

---

**현재 상태**: Dev 환경만 구축 완료. Prod 환경은 미구축.
