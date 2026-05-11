# Bootstrap 체크리스트 - 완전 자동화

## 목표
새로운 AWS 계정/환경에서 `./scripts/bootstrap-dev.sh` 한 번 실행으로 Agent T 서비스 전체를 배포할 수 있도록 구성.

---

## 사전 요구사항 (수동, 1회)

### 1. AWS 계정 및 인증
- [ ] AWS 계정 생성
- [ ] IAM 사용자 생성 (AdministratorAccess 또는 필요 권한)
- [ ] AWS CLI 설치
- [ ] `aws configure` 실행 (Access Key, Secret Key 설정)

### 2. 도구 설치
```bash
# macOS
brew install terraform kubectl helm

# Linux
# terraform: https://developer.hashicorp.com/terraform/install
# kubectl: https://kubernetes.io/docs/tasks/tools/
# helm: https://helm.sh/docs/intro/install/
```

### 3. Bedrock 모델 액세스 활성화 (1회, 5분)
```
AWS Console → Amazon Bedrock → Model access → Manage model access
→ Claude 3.5 Sonnet, Claude 3 Opus 체크 → Request model access
```

### 4. Terraform Backend 초기화 (자동화 가능, 하지만 최초 1회만)
```bash
# 이미 bootstrap 스크립트에 포함될 수 있지만, 
# 순환 참조 방지를 위해 수동으로 먼저 실행 권장
cd infra/terraform/envs/dev
terraform init  # 로컬 backend 사용
terraform apply -target=aws_s3_bucket.terraform_state  # S3 버킷 생성
# 이후 backend "s3" 블록 활성화 후 terraform init -migrate-state
```

---

## Bootstrap 실행

```bash
cd /path/to/agent-t
./scripts/bootstrap-dev.sh
```

**예상 소요 시간**: 25-30분
- Step 1: 환경 확인 (1분)
- Step 2: Terraform 인프라 구성 (20분)
- Step 3: Kubeconfig 동기화 (1분)
- Step 4: 플랫폼 컴포넌트 설치 (3분)
- Step 5: Argo CD Applications 등록 (1분)

---

## Bootstrap이 자동으로 생성하는 리소스

### AWS 인프라 (Terraform)
- [x] VPC, Subnets, NAT Gateway, Internet Gateway
- [x] EKS Cluster (v1.30) + Managed Node Groups (t3.medium x2)
- [x] RDS PostgreSQL (db.t4g.micro)
- [x] ElastiCache Redis (cache.t4g.micro)
- [x] S3 Buckets (artifact, rag_source, reports, model_data)
- [x] ECR Repositories (frontend, api-service, agent-service, simulation-service, analysis-service, report-service, simulation-runner)
- [x] Secrets Manager Secrets (db_credentials, redis_auth, app_secrets, bedrock_config)
- [x] VPC Endpoints (S3, ECR-API, ECR-DKR, Secrets Manager, STS, KMS, CloudWatch Logs)
- [x] IAM Roles for Service Accounts (IRSA)
  - ALB Controller → ALB/ELB/EC2 권한
  - Agent Service → Bedrock 권한
  - 기타 서비스 → S3, Secrets Manager 권한
- [x] Security Groups (EKS Cluster, Nodes, RDS, Redis, VPC Endpoints)
- [x] Route 53 Hosted Zone (선택적, `enable_route53=true`)
- [x] ACM SSL 인증서 (선택적, `enable_acm=true`)

### Kubernetes 리소스
- [x] Namespaces (kube-system, argocd, agent-t)
- [x] AWS Load Balancer Controller (Helm Chart)
- [x] Argo CD (Helm Chart)
- [x] Argo CD Applications (6개 서비스)

---

## Bootstrap 완료 후 확인

### 1. 인프라 확인
```bash
cd infra/terraform/envs/dev

# 모든 리소스 정상 생성 확인
terraform output

# 주요 Output
# - cluster_name: agent-t-dev-eks
# - cluster_endpoint: https://...
# - vpc_id: vpc-xxx
# - rds_endpoint: xxx.rds.amazonaws.com:5432
# - redis_endpoint: xxx.cache.amazonaws.com:6379
# - ecr_repository_urls: {...}
# - route53_name_servers: [...]  (enable_route53=true 시)
# - acm_certificate_arn: arn:aws:acm:...  (enable_acm=true 시)
```

### 2. Kubernetes 클러스터 확인
```bash
# Context 확인
kubectl config current-context
# agent-t-dev

# Nodes 확인
kubectl get nodes
# NAME                                             STATUS   AGE
# ip-10-10-x-x.ap-northeast-2.compute.internal     Ready    5m
# ip-10-10-x-x.ap-northeast-2.compute.internal     Ready    5m

# 모든 Pods 확인
kubectl get pods -A
# NAMESPACE        NAME                                            READY   STATUS
# kube-system      aws-load-balancer-controller-xxx                1/1     Running
# kube-system      aws-node-xxx                                    1/1     Running
# kube-system      coredns-xxx                                     1/1     Running
# kube-system      kube-proxy-xxx                                  1/1     Running
# argocd           argocd-server-xxx                               1/1     Running
# argocd           argocd-repo-server-xxx                          1/1     Running
# argocd           argocd-application-controller-xxx               1/1     Running
```

### 3. Argo CD 접속
```bash
# Argo CD Ingress 주소 확인
kubectl get ingress -n argocd
# NAME            ADDRESS
# argocd-server   k8s-argocd-xxx.ap-northeast-2.elb.amazonaws.com

# 브라우저에서 접속 (HTTP)
open http://$(kubectl get ingress argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# 초기 비밀번호
kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

### 4. Applications 확인
```bash
kubectl get applications -n argocd
# NAME                 SYNC STATUS   HEALTH STATUS
# frontend             Unknown       Healthy
# api-service          Unknown       Healthy
# agent-service        Unknown       Healthy
# simulation-service   Unknown       Healthy
# analysis-service     Unknown       Healthy
# report-service       Unknown       Healthy
```

**SYNC STATUS가 Unknown인 이유**: Git Repository에 Kubernetes Manifests가 아직 없음
→ 다음 단계에서 추가 필요

---

## 현재 미구현 (Bootstrap 이후 수동 작업)

### 1. 애플리케이션 Deployment
- [ ] Kubernetes Manifests 작성 (Deployment, Service, Ingress)
- [ ] 이미지 빌드 및 ECR 푸시
- [ ] Argo CD Sync

### 2. 도메인 연결 (선택적)
- [ ] Route 53 NS 레코드를 다른 계정에 설정
- [ ] DNS 전파 대기 (1-2시간)
- [ ] ACM 인증서 검증 완료 확인
- [ ] Ingress에 ACM ARN 추가

### 3. Secrets 값 주입
```bash
# Bedrock 설정
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-bedrock-config \
  --secret-string '{"model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"}'

# 외부 API Keys (필요 시)
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-app-secrets \
  --secret-string '{"openai_api_key": "sk-..."}'
```

---

## 비용 (dev 환경, 월간)

| 리소스 | 예상 비용 |
|--------|----------|
| EKS Cluster | $73 |
| EC2 (t3.medium x2) | $60 |
| NAT Gateway | $32 |
| RDS (db.t4g.micro) | $15 |
| Redis (cache.t4g.micro) | $12 |
| S3 | $5 |
| VPC Endpoints | $14 (2개 x $7) |
| Route 53 (선택) | $0.50 |
| **Total** | **~$211/월** |

**비용 절감 옵션**:
- NAT Gateway 비활성화 (VPC Endpoint만 사용): -$32
- EKS Fargate 사용 (EC2 대신): ~$80/월로 감소 가능
- Spot Instances: -30% EC2 비용

---

## 트러블슈팅

### Bootstrap 실패 시
```bash
# 어느 단계에서 실패했는지 확인
cat .bootstrap-checkpoint

# 해당 단계부터 재실행 (checkpoint 자동 인식)
./scripts/bootstrap-dev.sh
```

### Terraform 오류
```bash
cd infra/terraform/envs/dev

# State lock 해제
aws dynamodb delete-item \
  --table-name agent-t-terraform-locks \
  --key '{"LockID": {"S": "agent-t-terraform-state-dev/dev/terraform.tfstate"}}'

# 다시 실행
terraform apply
```

### Argo CD 접속 불가
```bash
# Pod 상태 확인
kubectl get pods -n argocd

# 로그 확인
kubectl logs -n argocd deploy/argocd-server
```

### ALB 생성 안됨 (Ingress ADDRESS 없음)
```bash
# ALB Controller 로그
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# IAM 권한 확인
aws iam get-policy-version \
  --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/agent-t-dev-alb-controller-policy \
  --version-id v1
```

---

## 다음 단계

### 1. 외부 접속 설정 (Frontend 배포)

#### 1.1 Argo CD 재배포 (Internal로 변경)
```bash
# 기존 internet-facing ingress 삭제
kubectl delete ingress -n argocd argocd-server 2>/dev/null || true

# Argo CD 재설치 (ingress disabled)
cd scripts
./install-platform.sh
```

#### 1.2 Frontend Ingress 배포
```bash
# Argo CD Application이 자동으로 배포
# 또는 수동 배포:
cd infra/helm/services/frontend
helm upgrade --install frontend . \
  -f values.yaml \
  -f values-dev.yaml \
  --namespace agent-t \
  --create-namespace
```

#### 1.3 ALB DNS 확인 (3-5분 소요)
```bash
kubectl get ingress -n agent-t frontend \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# 출력 예시: k8s-agentt-frontend-abc123.ap-northeast-2.elb.amazonaws.com
```

#### 1.4 Route 53 A 레코드 생성 (다른 계정, 수동)
```
1. AWS Console → Route 53 → Hosted zones → seolphung.com
2. Create record
   - Record name: @ (또는 비워둠)
   - Record type: A
   - Alias: Yes
   - Route traffic to: Application and Classic Load Balancer
   - Region: Asia Pacific (Seoul)
   - Load balancer: k8s-agentt-frontend-xxx 선택
3. Create records
```

#### 1.5 접속 테스트
```bash
# DNS 전파 확인 (1-5분)
dig seolphung.com

# HTTP 접속
curl -I http://seolphung.com

# 브라우저
open http://seolphung.com
```

#### 1.6 Argo CD 접속 (Port Forward)
```bash
# Port forward 시작
kubectl port-forward -n argocd svc/argocd-server 8080:80

# 브라우저
open http://localhost:8080

# 초기 비밀번호
kubectl get secret -n argocd argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

### 2. CI/CD 테스트

#### 2.1 GitHub Repository Secrets 설정
```bash
# GitHub → Settings → Secrets and variables → Actions
AWS_ACCESS_KEY_ID: AKIASYWOIAWEV7AC6YYM
AWS_SECRET_ACCESS_KEY: (Access Key Secret)
```

#### 2.2 코드 변경 후 푸시
```bash
cd apps/frontend
# ... 코드 수정 ...
git add .
git commit -m "feat: update frontend UI"
git push origin main
```

#### 2.3 자동 배포 확인
```
1. GitHub Actions 실행 (3-5분)
   - 테스트
   - 이미지 빌드
   - ECR 푸시
   - values-dev.yaml 업데이트

2. Argo CD 자동 배포 (3분 이내)
   - Git 변경 감지
   - Helm sync
   - Rolling update
```

### 3. 나머지 서비스 배포
- API Service, Agent Service 등도 동일하게 Ingress 추가
- 같은 ALB에 path-based routing으로 통합 가능

### 4. 모니터링 설정
   - Prometheus + Grafana
   - Loki (로그 수집)
   - Alertmanager

### 5. Production 환경 구성
   - `infra/terraform/envs/prod` 복사
   - 고가용성 설정 (Multi-AZ, 여러 Node Groups)
   - HTTPS 필수 (ACM + Route 53)
   - Backup 설정 (RDS Snapshot, S3 Versioning)
