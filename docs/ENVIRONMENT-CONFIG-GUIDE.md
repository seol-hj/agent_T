# 환경별 설정 전환 가이드

**목적**: Local, Dev, Prod 환경 간 전환 시 변경해야 할 설정 및 작업 방법

---

## 환경 개요

| 환경 | 인프라 | 설정 파일 | 배포 방법 |
|---|---|---|---|
| **Local** | Docker Compose | `docker-compose.yaml`, `.env.local` | `docker compose up` |
| **Dev** | AWS EKS | `infra/terraform/envs/dev/`, `values-dev.yaml` | Terraform + Argo CD |
| **Prod** | AWS EKS | `infra/terraform/envs/prod/`, `values-prod.yaml` | Terraform + Argo CD (수동) |

---

## 1. Local 환경 (개발/테스트)

### 목적
- 로컬 머신에서 빠른 개발/디버깅
- AWS 비용 없이 전체 시스템 테스트
- Mock LLM으로 Bedrock 호출 없이 동작 확인

### 설정 파일

#### `docker-compose.yaml`
```yaml
services:
  frontend:
    environment:
      - ENV=local
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NODE_ENV=development
    ports:
      - "3000:3000"
  
  api-service:
    environment:
      - ENV=local
      - LLM_PROVIDER=mock
      - STORAGE_PROVIDER=local
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=agent_t
      - DB_USER=agent_t
      - DB_PASSWORD=agent_t_pass
      - STORAGE_PATH=/data
    ports:
      - "8000:8000"
  
  agent-service:
    environment:
      - ENV=local
      - LLM_PROVIDER=mock  # MockLLMProvider 사용
      - STORAGE_PROVIDER=local
    ports:
      - "8000:8000"
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=agent_t
      - POSTGRES_USER=agent_t
      - POSTGRES_PASSWORD=agent_t_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
  local_storage:
```

#### `.env.local` (선택 사항)
```bash
# 애플리케이션
ENV=local
LOG_LEVEL=debug

# LLM (Mock)
LLM_PROVIDER=mock
LLM_MODEL=mock-claude-3.5

# Storage (Local)
STORAGE_PROVIDER=local
STORAGE_PATH=/data

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=agent_t
DB_USER=agent_t
DB_PASSWORD=agent_t_pass

# Redis (선택)
REDIS_HOST=redis
REDIS_PORT=6379
```

### 실행 방법

```bash
# 1. 전체 시스템 시작
docker compose up --build

# 2. 백그라운드 실행
docker compose up -d

# 3. 로그 확인
docker compose logs -f

# 4. 개별 서비스 재시작
docker compose restart frontend

# 5. 중지
docker compose down

# 6. 볼륨 포함 완전 삭제
docker compose down -v
```

### 접속

```bash
# Frontend
http://localhost:3000

# API Service
http://localhost:8000/docs

# Agent Service (Mock LLM)
curl http://localhost:8000/generate -d '{"prompt":"test"}'
```

### 변경 사항 반영

```bash
# 코드 변경 후
docker compose build <service-name>
docker compose up -d <service-name>

# 또는 전체 재빌드
docker compose up --build
```

---

## 2. Dev 환경 (통합 테스트)

### 목적
- 실제 AWS 환경에서 통합 테스트
- 실제 Bedrock LLM 호출
- 팀 공유 개발 환경
- CI/CD 파이프라인 검증

### 설정 파일

#### Terraform: `infra/terraform/envs/dev/terraform.tfvars`
```hcl
# 프로젝트 정보
project_name = "agent-t"
environment  = "dev"
aws_region   = "ap-northeast-2"

# EKS 설정
eks_cluster_version     = "1.33"
eks_node_instance_types = ["t3.medium"]
eks_min_size            = 2
eks_max_size            = 4

# RDS 설정
rds_instance_class          = "db.t3.micro"
rds_multi_az                = false  # 비용 절감
rds_backup_retention_period = 7

# Redis 설정
redis_node_type         = "cache.t3.micro"
redis_num_cache_nodes   = 1

# S3 버킷
s3_versioning_enabled = false  # 비용 절감

# 태그
tags = {
  Environment = "dev"
  ManagedBy   = "Terraform"
  Project     = "agent-t"
}
```

#### Helm: `infra/helm/services/*/values-dev.yaml`

**예시: frontend/values-dev.yaml**
```yaml
replicaCount: 1  # 최소 replica

image:
  repository: 190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/frontend
  tag: "sha-xxxxxxx"  # CI에서 자동 업데이트

serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::190484841865:role/agent-t-dev-frontend-irsa"

resources:
  requests:
    cpu: 50m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi

autoscaling:
  enabled: false

config:
  LOG_LEVEL: "debug"
  ENV: "dev"
  DB_HOST: "agent-t-dev-postgres.xxxxxx.ap-northeast-2.rds.amazonaws.com"
  REDIS_HOST: "agent-t-dev-redis.xxxxxx.cache.amazonaws.com"
  S3_BUCKET_RAG_SOURCE: "agent-t-dev-rag-source"
  S3_BUCKET_ARTIFACT: "agent-t-dev-artifact"
  S3_BUCKET_REPORTS: "agent-t-dev-reports"
  # LLM_PROVIDER: "bedrock"  # 자동 주입 (Gateway에서 설정)
  # STORAGE_PROVIDER: "s3"   # 자동 주입

secrets:
  dbSecretArn: "arn:aws:secretsmanager:ap-northeast-2:190484841865:secret:agent-t-dev-db-credentials"
  redisSecretArn: "arn:aws:secretsmanager:ap-northeast-2:190484841865:secret:agent-t-dev-redis-auth"
  appSecretArn: "arn:aws:secretsmanager:ap-northeast-2:190484841865:secret:agent-t-dev-app-secrets"

ingress:
  enabled: true
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
  hosts:
    - host: agent.seolphung.com
```

### 인프라 구축

```bash
# 1. Terraform 디렉토리로 이동
cd infra/terraform/envs/dev

# 2. 초기화
terraform init

# 3. 계획 확인
terraform plan

# 4. 인프라 구축
terraform apply

# 5. 출력 확인
terraform output
```

### 서비스 배포

```bash
# 1. EKS 접속 설정
aws eks update-kubeconfig --name agent-t-dev --region ap-northeast-2

# 2. 네임스페이스 확인
kubectl get namespaces

# 3. Argo CD Applications 등록
kubectl apply -f infra/argocd/applications/dev/

# 4. Argo CD 동기화 확인
kubectl get applications -n argocd

# 5. Pod 상태 확인
kubectl get pods -n default
```

### CI/CD 동작

**코드 변경 후:**
```bash
# main 브랜치에 push
git push origin main
```

**자동 실행:**
1. GitHub Actions 트리거
2. Docker build (루트 context)
3. ECR push: `agent-t-dev/<service>:sha-xxxxxxx`
4. gitops/dev 브랜치 업데이트
5. Argo CD 자동 sync (3분 이내)
6. Pod 재시작

### 접속

```bash
# HTTPS (권장)
https://agent.seolphung.com

# Argo CD 대시보드
kubectl port-forward -n argocd svc/argocd-server 8080:80
# http://localhost:8080
```

### 변경 사항 반영

**코드 변경:**
```bash
# 1. 코드 수정
vi apps/frontend/src/app/page.tsx

# 2. main에 push
git add .
git commit -m "feat: update frontend"
git push origin main

# 3. GitHub Actions 확인
# https://github.com/seol-hj/agent_T/actions

# 4. gitops/dev 확인 (자동 업데이트)
git checkout gitops/dev
git pull origin gitops/dev
cat infra/helm/services/frontend/values-dev.yaml | grep tag

# 5. Argo CD sync 대기 (3분)
kubectl get pods -w
```

**Helm values 변경:**
```bash
# 1. gitops/dev 브랜치에서 수정
git checkout gitops/dev
vi infra/helm/services/frontend/values-dev.yaml

# 2. 커밋 & push
git add .
git commit -m "chore: update frontend resources"
git push origin gitops/dev

# 3. Argo CD 자동 sync (3분)
```

---

## 3. Prod 환경 (프로덕션)

### 목적
- 실제 서비스 운영
- 고가용성 (HA)
- 프로덕션 워크로드

### 설정 파일

#### Terraform: `infra/terraform/envs/prod/terraform.tfvars`
```hcl
# 프로젝트 정보
project_name = "agent-t"
environment  = "prod"
aws_region   = "ap-northeast-2"

# EKS 설정
eks_cluster_version     = "1.33"
eks_node_instance_types = ["t3.large", "t3.xlarge"]
eks_min_size            = 4
eks_max_size            = 20

# RDS 설정
rds_instance_class          = "db.r6g.large"
rds_multi_az                = true  # HA 필수
rds_backup_retention_period = 30

# Redis 설정
redis_node_type           = "cache.r6g.large"
redis_num_cache_clusters  = 2  # Cluster mode

# S3 버킷
s3_versioning_enabled   = true
s3_lifecycle_enabled    = true

# 모니터링
enable_cloudwatch_alarms = true

# WAF
enable_waf = true

# 태그
tags = {
  Environment = "prod"
  ManagedBy   = "Terraform"
  Project     = "agent-t"
  CostCenter  = "engineering"
}
```

#### Helm: `infra/helm/services/*/values-prod.yaml` (작성 필요)

```yaml
replicaCount: 3  # 최소 3개 (HA)

image:
  repository: 190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-prod/frontend
  tag: "v1.0.0"  # Semantic versioning

serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::190484841865:role/agent-t-prod-frontend-irsa"

resources:
  requests:
    cpu: 200m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

config:
  LOG_LEVEL: "info"  # 최소 로그
  ENV: "prod"
  DB_HOST: "agent-t-prod-postgres.xxxxxx.ap-northeast-2.rds.amazonaws.com"
  REDIS_HOST: "agent-t-prod-redis.xxxxxx.cache.amazonaws.com"
  S3_BUCKET_RAG_SOURCE: "agent-t-prod-rag-source"
  S3_BUCKET_ARTIFACT: "agent-t-prod-artifact"
  S3_BUCKET_REPORTS: "agent-t-prod-reports"

secrets:
  dbSecretArn: "arn:aws:secretsmanager:ap-northeast-2:190484841865:secret:agent-t-prod-db-credentials"
  redisSecretArn: "arn:aws:secretsmanager:ap-northeast-2:190484841865:secret:agent-t-prod-redis-auth"
  appSecretArn: "arn:aws:secretsmanager:ap-northeast-2:190484841865:secret:agent-t-prod-app-secrets"

ingress:
  enabled: true
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:190484841865:certificate/PROD_CERT_ARN
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'  # HTTPS only
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:...  # WAF
  hosts:
    - host: agent.seolphung.com

podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

### 배포 방법 (수동 승인)

```bash
# 1. Release 태그 생성
git tag v1.0.0
git push origin v1.0.0

# 2. GitHub Actions (Manual Approval)
# https://github.com/seol-hj/agent_T/actions
# "Approve deployment to prod" 클릭

# 3. ECR 이미지 확인
aws ecr describe-images \
  --repository-name agent-t-prod/frontend \
  --region ap-northeast-2 \
  --image-ids imageTag=v1.0.0

# 4. gitops/prod 브랜치에 PR 생성
git checkout -b release/v1.0.0
# values-prod.yaml 업데이트
git add infra/helm/services/*/values-prod.yaml
git commit -m "chore: release v1.0.0"
git push origin release/v1.0.0

# 5. PR 리뷰 & Merge
# https://github.com/seol-hj/agent_T/pulls

# 6. Argo CD 수동 Sync (Auto Sync 금지)
kubectl apply -f infra/argocd/applications/prod/
# Argo CD UI에서 Manual Sync
```

---

## 환경 전환 비교표

### 설정 차이

| 항목 | Local | Dev | Prod |
|---|---|---|---|
| **배포** | `docker compose up` | `git push → CI/CD` | `git tag → Manual` |
| **Replica** | 1 | 1 | 3+ |
| **Auto Scale** | 없음 | 없음 | HPA |
| **LLM** | Mock | Bedrock | Bedrock |
| **Storage** | Local FS | S3 | S3 + Versioning |
| **DB** | Postgres 컨테이너 | RDS Single-AZ | RDS Multi-AZ |
| **Redis** | 없음 | ElastiCache 단일 | ElastiCache Cluster |
| **도메인** | localhost | agent.seolphung.com | agent.seolphung.com |
| **HTTPS** | 없음 | ACM | ACM + WAF |
| **로그 레벨** | debug | debug | info |
| **Monitoring** | 없음 | 기본 | CloudWatch + Alarms |
| **백업** | 없음 | 7일 | 30일 |
| **비용** | 무료 | ~$100/월 | ~$500/월 |

### 변경해야 할 파일

#### Local → Dev
```
❌ 삭제 불필요: docker-compose.yaml (로컬 전용)
✅ Terraform 실행: infra/terraform/envs/dev/
✅ Helm values 생성: infra/helm/services/*/values-dev.yaml (이미 작성됨)
✅ GitHub Secrets 설정: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
```

#### Dev → Prod
```
✅ Terraform 복사: infra/terraform/envs/prod/terraform.tfvars 수정
✅ Helm values 생성: infra/helm/services/*/values-prod.yaml 작성
✅ Argo CD App 생성: infra/argocd/applications/prod/
✅ ECR 분리: agent-t-prod/* 레포지토리
✅ Secrets Manager 분리: agent-t-prod-* secrets
✅ 인증서 분리: ACM 새로 발급 (prod용)
✅ CI/CD 수정: Manual approval 추가
```

---

## 환경 변수 주입 방식

### Local
```yaml
# docker-compose.yaml
services:
  frontend:
    environment:
      - ENV=local
      - LLM_PROVIDER=mock
```

### Dev/Prod
```yaml
# Kubernetes ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend
data:
  ENV: "dev"  # 또는 "prod"
  LLM_PROVIDER: "bedrock"

# IRSA로 AWS 인증 (자동 주입)
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::xxx:role/agent-t-dev-frontend-irsa"
```

---

## 작업 체크리스트

### Local 환경 시작
- [ ] `docker compose up --build` 실행
- [ ] http://localhost:3000 접속 확인
- [ ] Mock LLM 응답 확인

### Dev 환경 배포
- [ ] Terraform apply (`infra/terraform/envs/dev/`)
- [ ] EKS 접속 설정
- [ ] Argo CD Applications 등록
- [ ] GitHub Secrets 설정
- [ ] main 브랜치 push → CI/CD 동작 확인
- [ ] https://agent.seolphung.com 접속 확인

### Prod 환경 배포 (미구축)
- [ ] Terraform apply (`infra/terraform/envs/prod/`)
- [ ] values-prod.yaml 작성 (6개 서비스)
- [ ] Argo CD prod Applications 생성
- [ ] ECR prod 레포지토리 생성
- [ ] Secrets Manager prod secrets 생성
- [ ] ACM 인증서 발급 (prod용)
- [ ] CI/CD Manual approval 추가
- [ ] Release 태그 생성 → 배포

---

**다음 문서**: `docs/DOMAIN-SETUP-CHECK.md` (도메인 네임서버 확인)
