# Agent T 배포 가이드

AI Agent T 플랫폼을 AWS EKS에 배포하는 전체 프로세스.

---

## 📋 사전 준비

### 1. 필수 도구 설치

```bash
# 환경 확인 스크립트 실행
./scripts/check-env.sh

# 또는 수동 설치:

# Terraform
brew install terraform  # macOS
# or download from https://www.terraform.io/downloads

# AWS CLI
brew install awscli

# kubectl
brew install kubectl

# Helm
brew install helm

# Argo CD CLI (Optional)
brew install argocd
```

### 2. AWS 계정 설정

```bash
# AWS 인증 정보 설정
aws configure

# 입력 정보:
# - AWS Access Key ID: <your-access-key>
# - AWS Secret Access Key: <your-secret-key>
# - Default region: ap-northeast-2
# - Default output format: json
```

### 3. GitHub Repository 준비

```bash
# 저장소 클론
git clone https://github.com/YOUR_ORG/agent-t.git
cd agent-t

# develop 브랜치로 전환
git checkout develop
```

---

## 🚀 빠른 배포 (자동화 스크립트)

전체 환경을 자동으로 구축하려면 bootstrap 스크립트를 사용하세요:

```bash
# 1. 환경 확인
./scripts/check-env.sh

# 2. AWS 인증 설정
aws configure

# 3. 전체 환경 구축 (20-30분 소요)
./scripts/bootstrap-dev.sh
```

자세한 내용: [docs/troubleshooting.md](./docs/troubleshooting.md)

---

## 🔧 수동 배포 (단계별)

### 1단계: Terraform 인프라 구축

#### 1.1 Terraform 변수 파일 생성

```bash
cd infra/terraform/envs/dev

# terraform.tfvars 생성 (예시)
cat > terraform.tfvars << EOF
# 프로젝트 기본 정보
project     = "agent-t"
environment = "dev"
region      = "ap-northeast-2"

# VPC 설정
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["ap-northeast-2a", "ap-northeast-2b", "ap-northeast-2c"]

# EKS 설정
eks_cluster_version = "1.30"
eks_node_groups = {
  general = {
    desired_size = 2
    min_size     = 1
    max_size     = 4
    instance_types = ["t3.medium"]
  }
}

# RDS 설정
rds_instance_class    = "db.t3.micro"
rds_allocated_storage = 20
rds_database_name     = "agent_t_dev"

# Redis 설정
redis_node_type      = "cache.t3.micro"
redis_num_cache_nodes = 1

# S3 버킷 이름
s3_artifact_bucket   = "agent-t-dev-artifact"
s3_rag_source_bucket = "agent-t-dev-rag-source"
s3_reports_bucket    = "agent-t-dev-reports"

# Tags
tags = {
  Project     = "agent-t"
  Environment = "dev"
  ManagedBy   = "terraform"
}
EOF
```

#### 1.2 Terraform 실행

```bash
# 또는 스크립트 사용
./scripts/terraform-dev.sh init
./scripts/terraform-dev.sh plan
./scripts/terraform-dev.sh apply

# 수동 실행:
cd infra/terraform/envs/dev

# 초기화
terraform init

# 계획 확인
terraform plan -out=tfplan

# 인프라 생성 (20-30분 소요)
terraform apply tfplan
```

**생성되는 리소스**:
- VPC + Subnets (Public/Private/DB)
- NAT Gateway
- EKS Cluster (1.30)
- EKS Node Groups
- RDS PostgreSQL
- ElastiCache Redis
- S3 Buckets (3개)
- ECR Repositories (7개)
- VPC Endpoints (S3, ECR, Bedrock, Secrets Manager, STS, CloudWatch)
- IAM Roles (IRSA용)
- Security Groups

### 1.3 출력 정보 저장

```bash
# Terraform 출력값 확인
terraform output

# 주요 출력값:
# - eks_cluster_name: agent-t-dev-eks
# - eks_cluster_endpoint: https://xxx.eks.ap-northeast-2.amazonaws.com
# - rds_endpoint: agent-t-dev-postgres.xxx.rds.amazonaws.com
# - redis_endpoint: agent-t-dev-redis.xxx.cache.amazonaws.com
# - ecr_repository_urls: { agent-service: xxx.dkr.ecr.xxx, ... }
```

---

## 🔐 2단계: AWS Secrets Manager 설정

**참고**: bootstrap 스크립트 사용 시 이 단계는 자동으로 진행됩니다.

### 2.1 RDS 비밀번호 저장

```bash
aws secretsmanager create-secret \
  --name agent-t-dev-db-credentials \
  --description "Agent T Dev RDS Credentials" \
  --secret-string '{
    "username": "postgres",
    "password": "YOUR_STRONG_PASSWORD",
    "engine": "postgres",
    "host": "agent-t-dev-postgres.xxx.rds.amazonaws.com",
    "port": 5432,
    "dbname": "agent_t_dev"
  }' \
  --region ap-northeast-2
```

### 2.2 Redis 비밀번호 저장 (선택사항)

```bash
aws secretsmanager create-secret \
  --name agent-t-dev-redis-auth \
  --description "Agent T Dev Redis Auth" \
  --secret-string '{
    "auth_token": "YOUR_REDIS_TOKEN"
  }' \
  --region ap-northeast-2
```

### 2.3 애플리케이션 비밀 저장

```bash
aws secretsmanager create-secret \
  --name agent-t-dev-app-secrets \
  --description "Agent T Dev Application Secrets" \
  --secret-string '{
    "jwt_secret": "YOUR_JWT_SECRET",
    "api_key": "YOUR_API_KEY"
  }' \
  --region ap-northeast-2
```

---

## ☸️ 3단계: EKS 클러스터 설정

### 3.1 kubeconfig 동기화

```bash
# 프로젝트 루트로 이동
cd /path/to/agent-t

# kubeconfig 자동 설정
./scripts/sync-kubeconfig.sh

# 수동 설정 (선택사항)
aws eks update-kubeconfig \
  --name agent-t-dev-eks \
  --region ap-northeast-2
```

### 3.2 클러스터 접속 확인

```bash
# 노드 확인
kubectl get nodes

# 네임스페이스 확인
kubectl get namespaces
```

---

## 🚀 4단계: 플랫폼 컴포넌트 설치

### 4.1 AWS Load Balancer Controller 설치

```bash
./scripts/install-platform.sh alb

# 또는 수동 설치
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=agent-t-dev-eks \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="arn:aws:iam::YOUR_ACCOUNT:role/agent-t-dev-alb-controller"
```

### 4.2 Argo CD 설치

```bash
./scripts/install-platform.sh argocd

# 또는 수동 설치
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Argo CD admin 비밀번호 확인
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 4.3 Argo CD UI 접속

```bash
# 포트 포워딩
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 브라우저에서 https://localhost:8080 접속
# Username: admin
# Password: (위에서 확인한 비밀번호)
```

---

## 🐳 5단계: Docker 이미지 빌드 & ECR Push

**참고**: 
- v0.4.0부터 SUMO 실제 통합 완료 ✅
- Simulation Service는 SUMO 설치가 필요합니다 (Dockerfile에 포함)

### 5.1 ECR 로그인

```bash
# ECR 레지스트리 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com
```

### 5.2 서비스별 이미지 빌드 & Push

#### Agent Service

```bash
cd /path/to/agent-t

# 이미지 빌드
docker build -t agent-service:latest \
  -f apps/agent-service/Dockerfile .

# 태그
docker tag agent-service:latest \
  YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/agent-service:sha-$(git rev-parse --short HEAD)

# Push
docker push YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/agent-service:sha-$(git rev-parse --short HEAD)
```

#### Simulation Service

```bash
docker build -t simulation-service:latest \
  -f apps/simulation-service/Dockerfile .

docker tag simulation-service:latest \
  YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/simulation-service:sha-$(git rev-parse --short HEAD)

docker push YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/simulation-service:sha-$(git rev-parse --short HEAD)
```

#### Analysis Service

```bash
docker build -t analysis-service:latest \
  -f apps/analysis-service/Dockerfile .

docker tag analysis-service:latest \
  YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/analysis-service:sha-$(git rev-parse --short HEAD)

docker push YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/analysis-service:sha-$(git rev-parse --short HEAD)
```

#### Report Service

```bash
docker build -t report-service:latest \
  -f apps/report-service/Dockerfile .

docker tag report-service:latest \
  YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/report-service:sha-$(git rev-parse --short HEAD)

docker push YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/report-service:sha-$(git rev-parse --short HEAD)
```

### 5.3 이미지 태그를 Helm values에 반영

```bash
# 각 서비스의 values-dev.yaml 수정
# infra/helm/services/agent-service/values-dev.yaml
image:
  tag: "sha-abc123"  # 실제 Git SHA로 변경
```

---

## 📦 6단계: Helm Chart 환경 변수 설정

### 6.1 Agent Service 환경 변수

**파일**: `infra/helm/services/agent-service/values-dev.yaml`

```yaml
config:
  # 로그 레벨
  LOG_LEVEL: "info"  # debug/info/warning/error
  
  # 데이터베이스
  DB_HOST: "agent-t-dev-postgres.xxx.rds.amazonaws.com"
  DB_PORT: "5432"
  DB_NAME: "agent_t_dev"
  
  # Redis
  REDIS_HOST: "agent-t-dev-redis.xxx.cache.amazonaws.com"
  REDIS_PORT: "6379"
  
  # S3 버킷
  S3_BUCKET_RAG_SOURCE: "agent-t-dev-rag-source"
  S3_BUCKET_ARTIFACT: "agent-t-dev-artifact"
  S3_BUCKET_REPORTS: "agent-t-dev-reports"
  
  # LLM Gateway
  LLM_PROVIDER: "bedrock"  # bedrock/local
  LLM_MODEL_ID: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  LLM_REGION: "ap-northeast-2"
  
  # Storage Gateway
  STORAGE_PROVIDER: "s3"  # s3/local
  
  # 포트
  PORT: "8001"

secrets:
  # Secrets Manager ARN
  dbSecretArn: "arn:aws:secretsmanager:ap-northeast-2:YOUR_ACCOUNT:secret:agent-t-dev-db-credentials"
  redisSecretArn: "arn:aws:secretsmanager:ap-northeast-2:YOUR_ACCOUNT:secret:agent-t-dev-redis-auth"
  appSecretArn: "arn:aws:secretsmanager:ap-northeast-2:YOUR_ACCOUNT:secret:agent-t-dev-app-secrets"

serviceAccount:
  annotations:
    # IRSA 역할 ARN
    eks.amazonaws.com/role-arn: "arn:aws:iam::YOUR_ACCOUNT:role/agent-t-dev-agent-service-irsa"
```

### 6.2 Simulation Service 환경 변수

**파일**: `infra/helm/services/simulation-service/values-dev.yaml`

```yaml
config:
  LOG_LEVEL: "info"
  DB_HOST: "agent-t-dev-postgres.xxx.rds.amazonaws.com"
  REDIS_HOST: "agent-t-dev-redis.xxx.cache.amazonaws.com"
  S3_BUCKET_ARTIFACT: "agent-t-dev-artifact"
  
  # Storage
  STORAGE_PROVIDER: "s3"
  
  # SUMO Executor
  SUMO_EXECUTOR_TYPE: "kubernetes_job"  # kubernetes_job/dry_run
  
  # 포트
  PORT: "8005"

serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::YOUR_ACCOUNT:role/agent-t-dev-simulation-service-irsa"
```

### 6.3 Analysis Service 환경 변수

**파일**: `infra/helm/services/analysis-service/values-dev.yaml`

```yaml
config:
  LOG_LEVEL: "info"
  DB_HOST: "agent-t-dev-postgres.xxx.rds.amazonaws.com"
  S3_BUCKET_ARTIFACT: "agent-t-dev-artifact"
  STORAGE_PROVIDER: "s3"
  PORT: "8006"

serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::YOUR_ACCOUNT:role/agent-t-dev-analysis-service-irsa"
```

### 6.4 Report Service 환경 변수

**파일**: `infra/helm/services/report-service/values-dev.yaml`

```yaml
config:
  LOG_LEVEL: "info"
  DB_HOST: "agent-t-dev-postgres.xxx.rds.amazonaws.com"
  S3_BUCKET_REPORTS: "agent-t-dev-reports"
  
  # LLM
  LLM_PROVIDER: "bedrock"
  LLM_MODEL_ID: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  
  # Storage
  STORAGE_PROVIDER: "s3"
  
  PORT: "8007"

serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::YOUR_ACCOUNT:role/agent-t-dev-report-service-irsa"
```

---

## 🔄 7단계: Argo CD Applications 등록

### 7.1 Application 매니페스트 업데이트

**파일**: `infra/argocd/applications/dev/agent-service.yaml`

```yaml
spec:
  source:
    repoURL: https://github.com/YOUR_ORG/agent-t.git  # 실제 URL로 변경
    targetRevision: develop
```

모든 Application 매니페스트에 동일하게 적용.

### 7.2 Application 등록

```bash
# 자동 등록 스크립트 실행
./scripts/register-argocd-apps.sh

# 또는 수동 등록
kubectl apply -f infra/argocd/applications/dev/agent-service.yaml
kubectl apply -f infra/argocd/applications/dev/simulation-service.yaml
kubectl apply -f infra/argocd/applications/dev/analysis-service.yaml
kubectl apply -f infra/argocd/applications/dev/report-service.yaml
```

### 7.3 동기화 확인

```bash
# Argo CD CLI로 확인
argocd app list

# 수동 동기화 (필요시)
argocd app sync agent-service
argocd app sync simulation-service
argocd app sync analysis-service
argocd app sync report-service
```

---

## ✅ 8단계: 배포 확인

### 8.1 Pod 상태 확인

```bash
# 모든 Pod 확인
kubectl get pods

# 특정 서비스 Pod 확인
kubectl get pods -l app=agent-service
kubectl get pods -l app=simulation-service
kubectl get pods -l app=analysis-service
kubectl get pods -l app=report-service

# Pod 로그 확인
kubectl logs -f <pod-name>
```

### 8.2 Service 확인

```bash
# Service 목록
kubectl get svc

# Service 상세 정보
kubectl describe svc agent-service
```

### 8.3 Health Check

```bash
# 포트 포워딩으로 테스트
kubectl port-forward svc/agent-service 8001:8001

# 다른 터미널에서 Health Check
curl http://localhost:8001/health
curl http://localhost:8001/ready

# 결과 예시:
# {
#   "status": "healthy",
#   "service": "agent-service",
#   "timestamp": "2026-05-07T12:00:00.000Z",
#   "version": "0.3.0"
# }
```

### 8.4 모든 서비스 Health Check

```bash
# agent-service
kubectl port-forward svc/agent-service 8001:8001 &
curl http://localhost:8001/health

# simulation-service
kubectl port-forward svc/simulation-service 8005:8005 &
curl http://localhost:8005/health

# analysis-service
kubectl port-forward svc/analysis-service 8006:8006 &
curl http://localhost:8006/health

# report-service
kubectl port-forward svc/report-service 8007:8007 &
curl http://localhost:8007/health
```

---

## 🌐 9단계: Ingress 설정 (선택사항)

### 9.1 Ingress 리소스 생성

**파일**: `k8s/ingress/ingress-dev.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agent-t-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
    - host: api.agent-t-dev.example.com
      http:
        paths:
          - path: /agent
            pathType: Prefix
            backend:
              service:
                name: agent-service
                port:
                  number: 8001
          - path: /simulation
            pathType: Prefix
            backend:
              service:
                name: simulation-service
                port:
                  number: 8005
          - path: /analysis
            pathType: Prefix
            backend:
              service:
                name: analysis-service
                port:
                  number: 8006
          - path: /report
            pathType: Prefix
            backend:
              service:
                name: report-service
                port:
                  number: 8007
```

### 9.2 Ingress 적용

```bash
kubectl apply -f k8s/ingress/ingress-dev.yaml

# ALB 생성 확인 (2-3분 소요)
kubectl get ingress

# ALB DNS 확인
kubectl get ingress agent-t-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### 9.3 Route 53 설정 (선택사항)

AWS Route 53에서 도메인을 ALB DNS로 CNAME 레코드 추가.

---

## 🔍 10단계: 모니터링 & 로깅

### 10.1 CloudWatch Logs 확인

```bash
# CloudWatch Logs Group 확인
aws logs describe-log-groups --region ap-northeast-2

# 로그 스트림 확인
aws logs describe-log-streams \
  --log-group-name /aws/eks/agent-t-dev-eks/cluster \
  --region ap-northeast-2
```

### 10.2 Prometheus/Grafana 설치 (선택사항)

```bash
# Prometheus Helm Chart
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Grafana 접속
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# http://localhost:3000 (admin/prom-operator)
```

---

## 🔄 11단계: CI/CD 설정 (GitHub Actions)

### 11.1 GitHub Secrets 설정

GitHub Repository → Settings → Secrets and variables → Actions

**추가할 Secrets**:
- `AWS_ACCESS_KEY_ID`: AWS 액세스 키
- `AWS_SECRET_ACCESS_KEY`: AWS 시크릿 키
- `AWS_REGION`: ap-northeast-2
- `ECR_REGISTRY`: YOUR_ACCOUNT.dkr.ecr.ap-northeast-2.amazonaws.com

### 11.2 CI 워크플로우 활성화

모든 `.github/workflows/ci-*.yml` 파일이 자동으로 실행됨.

**트리거**:
- `develop` 브랜치에 push
- `main` 브랜치에 push
- Pull Request 생성

**동작**:
1. 코드 변경 감지
2. Docker 이미지 빌드
3. ECR에 Push (Git SHA 태그)
4. Argo CD가 자동으로 새 이미지 감지 및 배포

---

## 📊 환경 변수 요약

### 필수 환경 변수 (모든 서비스)

| 변수명 | 설명 | 예시값 |
|--------|------|--------|
| `LOG_LEVEL` | 로그 레벨 | `info` |
| `DB_HOST` | RDS 엔드포인트 | `agent-t-dev-postgres.xxx.rds.amazonaws.com` |
| `REDIS_HOST` | Redis 엔드포인트 | `agent-t-dev-redis.xxx.cache.amazonaws.com` |
| `STORAGE_PROVIDER` | 스토리지 제공자 | `s3` |

### Agent Service 추가 환경 변수

| 변수명 | 설명 | 예시값 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM 제공자 | `bedrock` |
| `LLM_MODEL_ID` | Bedrock 모델 ID | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `PORT` | 서비스 포트 | `8001` |

### Simulation Service 추가 환경 변수

| 변수명 | 설명 | 예시값 |
|--------|------|--------|
| `SUMO_EXECUTOR_TYPE` | SUMO 실행 타입 | `kubernetes_job` |
| `PORT` | 서비스 포트 | `8005` |

### Analysis Service 추가 환경 변수

| 변수명 | 설명 | 예시값 |
|--------|------|--------|
| `PORT` | 서비스 포트 | `8006` |

### Report Service 추가 환경 변수

| 변수명 | 설명 | 예시값 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM 제공자 | `bedrock` |
| `LLM_MODEL_ID` | Bedrock 모델 ID | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `PORT` | 서비스 포트 | `8007` |

---

## 🛠️ 문제 해결

### Pod가 CrashLoopBackOff 상태

```bash
# 로그 확인
kubectl logs <pod-name>

# 이벤트 확인
kubectl describe pod <pod-name>

# 일반적인 원인:
# 1. 환경 변수 누락
# 2. IRSA 역할 권한 부족
# 3. DB/Redis 연결 실패
# 4. 이미지 Pull 실패
```

### Secrets Manager 접근 실패

```bash
# IRSA 역할 확인
kubectl describe serviceaccount <service-name>

# 역할에 secretsmanager:GetSecretValue 권한 필요
```

### Bedrock 호출 실패

```bash
# VPC Endpoint 확인
aws ec2 describe-vpc-endpoints --region ap-northeast-2

# IRSA 역할에 bedrock:InvokeModel 권한 필요
```

---

## 🎯 배포 체크리스트

### 인프라
- [ ] Terraform 인프라 생성 완료
- [ ] VPC Endpoints 생성 확인
- [ ] EKS 클러스터 정상 동작
- [ ] RDS/Redis 생성 및 접근 가능
- [ ] S3 버킷 생성
- [ ] ECR 레포지토리 생성

### 보안
- [ ] Secrets Manager에 DB 비밀번호 저장
- [ ] IRSA 역할 생성 및 권한 설정
- [ ] Security Group 규칙 확인

### 애플리케이션
- [ ] 모든 서비스 Docker 이미지 빌드
- [ ] ECR에 이미지 Push
- [ ] Simulation Service SUMO 설치 확인 ✅ (v0.4.0)
- [ ] Helm values 환경 변수 설정
- [ ] Argo CD Applications 등록
- [ ] 모든 Pod Running 상태 확인
- [ ] Health Check 성공
- [ ] SUMO 실제 시뮬레이션 테스트 ✅ (v0.4.0)

### CI/CD
- [ ] GitHub Secrets 설정
- [ ] CI 워크플로우 정상 동작
- [ ] Argo CD 자동 동기화 확인

---

## 📚 추가 참고 자료

- [환경 재구축 가이드](./troubleshooting.md) - 전체 환경 자동 구축
- [SUMO 통합 가이드](./sumo-integration.md) - SUMO 실제 통합 상세 ✅
- [프로젝트 달성도 분석](./project-comparison.md) - 완성도 85%
- [Observability 아키텍처](./observability.md) - 로깅, 메트릭, 추적
- [빠른 시작 가이드](../QUICKSTART.md) - 로컬 실행

---

**배포 완료 후 확인사항**:
1. 모든 서비스 Health Check 통과
2. Argo CD에서 모든 Application Synced 상태
3. CloudWatch Logs에 로그 수집 확인
4. Bedrock 호출 정상 동작 (agent-service, report-service)
5. S3 파일 업로드 정상 동작 (모든 서비스)
6. **SUMO 시뮬레이션 실행 테스트** ✅ (v0.4.0)
   - OSM → SUMO 네트워크 변환 확인
   - 교통 수요 생성 확인
   - 실제 SUMO 시뮬레이션 실행 확인
   - KPI 추출 (21가지) 확인

**문제 발생 시**: [GitHub Issues](https://github.com/YOUR_ORG/agent-t/issues)
