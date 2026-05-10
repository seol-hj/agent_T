# Environment Rebuild Guide

새 컴퓨터 또는 새 AWS 계정에서 AI Agent T 플랫폼 전체 환경 재현 가이드.

> **재현 가능성**: 이 문서가 작동하지 않으면 프로젝트 운영에 문제가 있다는 신호.

**예상 소요 시간**: 2-3시간 (AWS 리소스 프로비저닝 포함)  
**예상 비용**: ~$150-200/월 (dev 환경)

---

## 개요

이 가이드는 다음 상황에서 사용한다:
- 새 개발 머신 설정
- 팀 멤버 온보딩
- CI/CD 환경 구성
- 재해 복구 (Disaster Recovery)

**목표**: `git clone` 후 스크립트 실행만으로 전체 환경 구축

---

## 사전 준비

### 1. AWS 계정 및 권한

다음 권한이 필요하다:
- **EKS**: 클러스터 생성/관리
- **EC2**: VPC, Subnets, Security Groups, NAT Gateway
- **RDS**: PostgreSQL 인스턴스
- **ElastiCache**: Redis 클러스터
- **S3**: 버킷 생성
- **ECR**: 레지스트리 생성
- **IAM**: Role, Policy 생성 (IRSA 포함)
- **Secrets Manager**: Secret 생성

**권장**: `AdministratorAccess` (dev 환경) 또는 커스텀 policy

### 2. AWS CLI 인증 설정

```bash
# AWS CLI 설치 (macOS)
brew install awscli

# AWS CLI 설치 (Linux)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 인증 설정
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: ap-northeast-2
# Default output format: json

# 인증 확인
aws sts get-caller-identity
```

### 3. Git repository 클론

```bash
git clone https://github.com/YOUR_ORG/agent-t.git
cd agent-t

# 브랜치 확인
git branch
# develop (dev 환경)
# main (prod 환경)

# dev 환경 작업 시
git checkout develop
```

---

## 필수 도구 설치

### macOS

```bash
# Homebrew (패키지 관리자)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 필수 CLI 도구
brew install \
  terraform \
  kubectl \
  helm \
  awscli \
  docker \
  jq

# Docker Desktop 설치
brew install --cask docker

# Docker Desktop 실행 (GUI)
open -a Docker
```

### Linux (Ubuntu/Debian)

```bash
# Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Docker
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# jq
sudo apt-get install jq
```

### Windows (WSL2 권장)

```powershell
# WSL2 활성화
wsl --install

# Ubuntu 설치
wsl --install -d Ubuntu-22.04

# WSL 내부에서 위 Linux 설치 스크립트 실행
```

---

## 자동 Bootstrap (권장)

전체 환경을 한 번에 구성한다.

```bash
# 1. 환경 확인
./scripts/check-env.sh

# 2. 자동 Bootstrap 실행
./scripts/bootstrap-dev.sh
```

**bootstrap-dev.sh가 수행하는 작업**:
1. 환경 확인 (check-env.sh)
2. Terraform 인프라 구성 (terraform-dev.sh)
3. Kubeconfig 동기화 (sync-kubeconfig.sh)
4. 플랫폼 설치 (install-platform.sh)
5. Argo CD Applications 등록 (register-argocd-apps.sh)

**소요 시간**: 약 20-30분 (AWS 리소스 생성 시간 포함)

**예상 비용**: ~$150-200/월 (dev 환경)

### Checkpoint 및 재시작

중간에 실패하면 자동으로 checkpoint가 저장된다. 재시작 시 이어서 진행 가능:

```bash
# 실패 후 재시작
./scripts/bootstrap-dev.sh

# 옵션 선택:
#   1) Step N부터 계속 (추천)
#   2) 처음부터 다시 시작
```

**Checkpoint 위치**: `.bootstrap-checkpoint` (프로젝트 루트)

**단계별 재시작 지점**:
- Step 1 실패 → 필수 도구 설치 후 재실행
- Step 2 실패 → Terraform 상태 확인 후 재실행 (멱등성 보장)
- Step 3 실패 → EKS 클러스터 생성 확인 후 재실행
- Step 4 실패 → Helm 차트 재설치 (uninstall → install)
- Step 5 실패 → Argo CD Applications 재적용

**수동으로 checkpoint 초기화**:
```bash
rm .bootstrap-checkpoint
./scripts/bootstrap-dev.sh
```

---

## 수동 단계별 실행 (디버깅/학습용)

자동 bootstrap 대신 단계별로 실행할 수 있다.

### Step 1: 환경 확인

```bash
./scripts/check-env.sh
```

**확인 항목**:
- ✓ AWS CLI
- ✓ Terraform
- ✓ kubectl
- ✓ Helm
- ✓ Docker
- ✓ jq
- ✓ Git
- ✓ AWS 인증
- ✓ Docker 데몬 실행

**실패 시**: 누락된 도구를 설치하고 다시 실행

### Step 2: Terraform 인프라 구성

```bash
./scripts/terraform-dev.sh
```

**수행 작업**:
1. `cd infra/terraform/envs/dev`
2. `terraform init`
3. `terraform plan`
4. 승인 대기 (사용자 확인)
5. `terraform apply`

**생성 리소스**:
- VPC (10.0.0.0/16)
  - Public Subnets x2
  - Private App Subnets x2
  - Private DB Subnets x2
  - NAT Gateway x2
  - Internet Gateway
- EKS Cluster (1.30)
  - Control Plane
  - Managed Node Group (2-4 nodes, t3.medium)
  - OIDC Provider (IRSA)
- RDS PostgreSQL (db.t3.micro, dev only)
- ElastiCache Redis (cache.t3.micro)
- S3 Buckets (scenarios, simulations, reports)
- ECR Repositories (7개 서비스)
- Secrets Manager (DB, Redis credentials)
- IAM Roles (각 서비스별 IRSA)

**소요 시간**: 15-20분

**확인**:
```bash
cd infra/terraform/envs/dev
terraform output
```

### Step 3: Kubeconfig 동기화

```bash
./scripts/sync-kubeconfig.sh
```

**수행 작업**:
1. Terraform output에서 EKS cluster name 가져오기
2. `aws eks update-kubeconfig` 실행
3. 클러스터 연결 확인
4. Node 상태 확인

**확인**:
```bash
kubectl cluster-info
kubectl get nodes
kubectl config current-context
```

### Step 4: 플랫폼 컴포넌트 설치

```bash
./scripts/install-platform.sh
```

**설치 항목**:
1. **AWS Load Balancer Controller**
   - Helm Chart: `aws-load-balancer-controller`
   - IRSA 역할 자동 감지
   - Ingress → ALB 변환

2. **Argo CD**
   - Helm Chart: `argo-cd`
   - High Availability 설정 (prod)
   - Slack Notifications 활성화 (prod)

**소요 시간**: 3-5분

**확인**:
```bash
# ALB Controller
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Argo CD
kubectl get pods -n argocd

# Argo CD 초기 비밀번호
kubectl get secret -n argocd argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

### Step 5: Argo CD Applications 등록

```bash
./scripts/register-argocd-apps.sh
```

**등록 방식 선택**:
1. **ApplicationSet** (권장): 모든 서비스 일괄 등록
2. **개별 Application**: 서비스별 수동 등록

**등록 리소스**:
- `infra/argocd/applications/dev/` (7개)
  - api-service
  - agent-service
  - simulation-service
  - analysis-service
  - report-service
  - frontend
  - gateway
- `infra/argocd/applicationsets/services-dev.yaml`

**확인**:
```bash
kubectl get applications -n argocd
kubectl get applicationsets -n argocd
```

---

## 배포 확인

### 1. Argo CD UI 접속

```bash
# Port Forward
kubectl port-forward -n argocd svc/argocd-server 8080:443

# 브라우저에서 열기
open https://localhost:8080
```

**로그인**:
- Username: `admin`
- Password: (위에서 확인한 초기 비밀번호)

### 2. Application 동기화 상태 확인

```bash
# CLI로 확인 (argocd CLI 필요)
argocd app list

# kubectl로 확인
kubectl get applications -n argocd

# 상세 확인
kubectl describe application api-service -n argocd
```

**정상 상태**:
- Health: `Healthy`
- Sync: `Synced`

### 3. 서비스 배포 확인

```bash
# Pods 확인
kubectl get pods

# Services 확인
kubectl get svc

# Ingress 확인
kubectl get ingress

# ALB 생성 확인
kubectl describe ingress gateway
```

### 4. 로그 확인

```bash
# Pod 로그
kubectl logs -f <pod-name>

# 여러 Pod 동시 확인
kubectl logs -f -l app=api-service

# Argo CD 로그
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

---

## Troubleshooting

### 1. check-env.sh 실패

**증상**: 도구 누락

**해결**:
```bash
# macOS
brew install <tool-name>

# Linux
sudo apt-get install <tool-name>
```

### 2. AWS 인증 실패

**증상**: `Unable to locate credentials`

**해결**:
```bash
aws configure

# 또는 환경 변수
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export AWS_DEFAULT_REGION=ap-northeast-2
```

### 3. Terraform 실패

**증상**: `Error creating VPC`, `Error creating EKS`

**원인**:
- 권한 부족
- Quota 초과
- 리전 제한

**해결**:
```bash
# 권한 확인
aws iam get-user
aws iam list-attached-user-policies --user-name <username>

# Quota 확인
aws service-quotas list-service-quotas \
  --service-code vpc \
  --query 'Quotas[?QuotaName==`VPCs per Region`]'

# 상태 확인
cd infra/terraform/envs/dev
terraform state list

# 부분 실패 시 재적용 (멱등성)
terraform apply

# 완전 초기화 (주의: 데이터 삭제)
terraform destroy -auto-approve
terraform apply
```

**재시작**:
```bash
# Checkpoint가 Step 2로 저장되어 있으면
./scripts/bootstrap-dev.sh  # Step 3부터 계속
```

### 4. Kubeconfig 동기화 실패

**증상**: `error: You must be logged in to the server`

**원인**:
- EKS 클러스터 미생성
- IAM 권한 부족
- 리전 불일치

**해결**:
```bash
# 클러스터 존재 확인
aws eks list-clusters --region ap-northeast-2

# 수동 업데이트
aws eks update-kubeconfig \
  --region ap-northeast-2 \
  --name agent-t-dev-eks

# 연결 확인
kubectl cluster-info
```

### 5. 플랫폼 설치 실패

**증상**: Helm install 실패, Pod CrashLoopBackOff

**원인**:
- IRSA 역할 미생성
- IAM Policy 미다운로드
- Image Pull 실패

**해결**:
```bash
# ALB Controller IAM Policy 다운로드
./scripts/download-alb-policy.sh

# IRSA 역할 확인
cd infra/terraform/envs/dev
terraform output irsa_roles

# Pod 상태 확인
kubectl describe pod <pod-name> -n kube-system

# 재설치
helm uninstall aws-load-balancer-controller -n kube-system
helm uninstall argocd -n argocd

# Checkpoint 조정 (Step 3으로 되돌림)
echo "3" > .bootstrap-checkpoint

# 재실행
./scripts/bootstrap-dev.sh  # Step 4부터 계속
```

### 6. Argo CD Applications OutOfSync

**증상**: Git과 클러스터 상태 불일치

**원인**:
- Git repository URL 오류 (YOUR_ORG 미교체)
- Branch 불일치
- Helm Chart 오류

**해결**:
```bash
# Git repository URL 확인
git remote get-url origin

# Applications 수정
vi infra/argocd/applications/dev/*.yaml
# repoURL: https://github.com/<real-org>/agent-t.git

# 재적용
kubectl apply -f infra/argocd/applications/dev/

# 수동 동기화
argocd app sync api-service

# Checkpoint 조정 (Step 4로 되돌림)
echo "4" > .bootstrap-checkpoint

# 재실행
./scripts/bootstrap-dev.sh  # Step 5부터 계속
```

---

## 정리 (Clean Up)

환경을 완전히 삭제한다 (비용 절감).

```bash
# 1. Argo CD Applications 삭제
kubectl delete applications -n argocd --all

# 2. 플랫폼 컴포넌트 삭제
helm uninstall argocd -n argocd
helm uninstall aws-load-balancer-controller -n kube-system

# 3. Terraform 리소스 삭제
cd infra/terraform/envs/dev
terraform destroy -auto-approve

# 4. Kubeconfig 정리
kubectl config delete-context agent-t-dev

# 5. Checkpoint 삭제
rm -f .bootstrap-checkpoint
```

**주의**: `terraform destroy`는 데이터를 영구 삭제한다 (S3, RDS, Redis)

---

## 참고 문서

- [EKS 클러스터 관리](./eks.md)
- [플랫폼 컴포넌트](./platform-components.md)
- [GitOps with Argo CD](./gitops.md)
- [CI/CD Pipeline](./cicd.md)

---

## FAQ

### Q1. 비용은 얼마나 드나요?

**Dev 환경** (최소 구성):
- EKS Control Plane: ~$73/월
- EC2 Node Groups (t3.medium x2): ~$60/월
- NAT Gateway x2: ~$65/월
- RDS (db.t3.micro): ~$15/월
- ElastiCache (cache.t3.micro): ~$12/월
- ALB: ~$20/월
- 기타 (S3, ECR, Secrets Manager): ~$10/월

**총 예상 비용**: ~$150-200/월

**Prod 환경** (HA 구성):
- ~$500-800/월

### Q2. 얼마나 걸리나요?

- **자동 bootstrap**: 20-30분
- **수동 단계별**: 30-40분

대부분의 시간은 AWS 리소스 생성 대기 (EKS, RDS, NAT Gateway)

### Q3. 여러 환경을 동시에 실행할 수 있나요?

**가능**:
```bash
# Dev 환경
ENV=dev ./scripts/bootstrap-dev.sh

# Prod 환경 (별도 터미널)
ENV=prod ./scripts/bootstrap-prod.sh
```

**주의**: 비용이 2배로 증가

### Q4. 로컬 개발 시 EKS 없이 가능한가요?

**가능** (Kind/K3d 사용):
```bash
# Kind 설치
brew install kind

# 로컬 클러스터 생성
kind create cluster --name agent-t-local

# Helm Charts 테스트
helm install api-service infra/helm/services/api-service \
  --values infra/helm/services/api-service/values-dev.yaml
```

**제약**:
- IRSA 불가 (AWS 리소스 접근 불가)
- ALB Ingress 불가
- RDS/Redis 대신 로컬 DB 필요

### Q5. Argo CD 없이 배포할 수 있나요?

**가능** (Helm 직접 사용):
```bash
# 각 서비스 수동 배포
helm install api-service infra/helm/services/api-service \
  --values infra/helm/services/api-service/values-dev.yaml

helm install gateway infra/helm/gateway \
  --values infra/helm/gateway/values-dev.yaml
```

**단점**:
- GitOps 자동 동기화 불가
- Self-Healing 불가
- 수동 배포 필요

---

## 다음 단계

환경 구성 후:
1. **서비스 코드 구현**: `apps/<service>/` 디렉토리에 실제 애플리케이션 코드 작성
2. **CI 파이프라인 테스트**: GitHub Actions로 빌드/배포 자동화 확인
3. **GitOps 워크플로우**: Helm values 수정 → Git push → Argo CD 자동 배포
4. **모니터링 구성**: Prometheus, Grafana 설치
5. **로깅 구성**: Fluent Bit, CloudWatch Logs

자세한 내용은 프로젝트 Roadmap 참조.
