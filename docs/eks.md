# EKS 클러스터 관리

Agent T 프로젝트의 **EKS 클러스터 설정, 접근, kubeconfig 관리** 방법을 설명한다.

---

## 개요

| 항목 | 설정 |
|---|---|
| **Kubernetes 버전** | 1.30 |
| **노드 위치** | VPC private-app subnet |
| **Control Plane** | AWS 관리형 (API 엔드포인트만 노출) |
| **Node Group** | Managed Node Group (일반 워크로드 + SUMO 컴퓨팅용) |
| **Add-ons** | vpc-cni, coredns, kube-proxy, eks-pod-identity-agent |
| **IRSA** | OIDC provider 활성화 (ServiceAccount ↔ IAM Role 연결) |

---

## 클러스터 엔드포인트 접근

EKS 클러스터 API 엔드포인트는 **public** 또는 **private** 접근을 설정할 수 있다.

### dev 환경
- **Public 접근**: 활성화 (개발 편의)
- **Private 접근**: 활성화 (VPC 내부에서도 접근 가능)
- **Public 접근 CIDR**: `0.0.0.0/0` (모든 IP 허용, 필요 시 회사 IP로 제한)

```hcl
cluster_endpoint_public_access       = true
cluster_endpoint_private_access      = true
cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]
```

### prod 환경
- **Public 접근**: 비활성화 권장 (보안)
- **Private 접근**: 활성화
- **접근 방법**: VPN, Direct Connect, 또는 Bastion Host

```hcl
cluster_endpoint_public_access  = false
cluster_endpoint_private_access = true
```

---

## kubeconfig 설정

### 1. AWS CLI로 kubeconfig 생성

EKS 클러스터에 접근하려면 `aws eks update-kubeconfig` 명령으로 kubeconfig를 생성한다.

```bash
# AWS CLI 인증 설정 (프로필 사용)
export AWS_PROFILE=agent-t-dev
export AWS_REGION=ap-northeast-2

# kubeconfig 생성
aws eks update-kubeconfig \
  --name agent-t-dev-eks \
  --region ap-northeast-2 \
  --alias agent-t-dev

# 생성 확인
kubectl config get-contexts
kubectl cluster-info
```

### 2. kubeconfig 파일 위치

기본 위치: `~/.kube/config`

여러 클러스터를 관리하는 경우:
```bash
# dev 클러스터
aws eks update-kubeconfig --name agent-t-dev-eks --alias agent-t-dev

# prod 클러스터
aws eks update-kubeconfig --name agent-t-prod-eks --alias agent-t-prod

# context 전환
kubectl config use-context agent-t-dev
kubectl config use-context agent-t-prod
```

### 3. 인증 메커니즘

kubeconfig에는 AWS IAM 인증 정보가 포함된다. `kubectl` 실행 시 AWS CLI가 자동으로 토큰을 생성한다.

```yaml
# ~/.kube/config 예시
users:
- name: arn:aws:eks:ap-northeast-2:123456789012:cluster/agent-t-dev-eks
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: aws
      args:
      - eks
      - get-token
      - --cluster-name
      - agent-t-dev-eks
      - --region
      - ap-northeast-2
```

**주의**: `aws eks get-token`이 실행되려면 AWS CLI 인증 정보(`AWS_PROFILE`, `~/.aws/credentials`)가 필요하다.

---

## IAM 권한 (kubectl 접근)

EKS 클러스터에 `kubectl`로 접근하려면 IAM 사용자/역할에 권한이 필요하다.

### 1. 클러스터 생성자

Terraform으로 EKS 클러스터를 생성한 IAM 사용자/역할은 자동으로 `system:masters` 그룹에 추가된다.

### 2. 추가 사용자 권한 부여

다른 IAM 사용자/역할에게 kubectl 접근 권한을 부여하려면 `aws-auth` ConfigMap을 수정한다.

```bash
kubectl edit configmap aws-auth -n kube-system
```

**예시: IAM 사용자 추가**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/developer
      username: developer
      groups:
        - system:masters
```

**예시: IAM 역할 추가**
```yaml
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/DevOpsRole
      username: devops
      groups:
        - system:masters
```

**Terraform으로 관리** (추후 구현 권장):
```hcl
resource "kubernetes_config_map_v1_data" "aws_auth" {
  metadata {
    name      = "aws-auth"
    namespace = "kube-system"
  }

  data = {
    mapUsers = yamlencode([...])
    mapRoles = yamlencode([...])
  }
}
```

---

## 노드 그룹

### dev 환경

| Node Group | 인스턴스 타입 | 개수 | 용도 |
|---|---|---|---|
| `general` | `t3.medium` | 2-4 | 일반 워크로드 (API, Agent, Analysis, Report) |

```hcl
node_groups = {
  general = {
    instance_types = ["t3.medium"]
    desired_size   = 2
    min_size       = 1
    max_size       = 4
    capacity_type  = "ON_DEMAND"
    labels = {
      workload = "general"
    }
  }
}
```

### prod 환경

| Node Group | 인스턴스 타입 | 개수 | 용도 |
|---|---|---|---|
| `general` | `m5.large` | 3-6 | 일반 워크로드 |
| `sumo-compute` | `c5.2xlarge` | 1-5 | SUMO 시뮬레이션 (CPU 집약적) |

```hcl
node_groups = {
  general = {
    instance_types = ["m5.large"]
    desired_size   = 3
    min_size       = 2
    max_size       = 6
    labels = {
      workload = "general"
    }
  }
  sumo-compute = {
    instance_types = ["c5.2xlarge"]
    desired_size   = 1
    min_size       = 0
    max_size       = 5
    labels = {
      workload = "sumo-compute"
    }
    taints = [
      {
        key    = "workload"
        value  = "sumo"
        effect = "NoSchedule"
      }
    ]
  }
}
```

**SUMO Compute Node Group**:
- Taint: `workload=sumo:NoSchedule` — 일반 Pod는 스케줄링되지 않음
- Toleration: SUMO Runner Pod만 이 노드에 배치됨
- Auto-scaling: SUMO 작업이 없을 때 0으로 축소 가능

---

## IRSA (IAM Roles for Service Accounts)

EKS Pod가 AWS 리소스(S3, RDS, Secrets Manager, Bedrock 등)에 접근하려면 **IRSA**를 사용한다.

### 동작 원리

1. EKS 클러스터는 **OIDC provider**를 생성
2. Kubernetes ServiceAccount에 **IAM Role ARN** annotation 추가
3. Pod가 해당 ServiceAccount를 사용하면 자동으로 IAM Role credentials 주입
4. AWS SDK가 자동으로 credentials 사용 (환경 변수 설정 불필요)

### 설정된 IRSA 목록

| ServiceAccount | Namespace | IAM Role | 권한 |
|---|---|---|---|
| `agent-service` | `default` | `agent-t-dev-agent-service-irsa` | Bedrock InvokeModel, S3 rag/artifact 읽기, Secrets Manager 읽기 |
| `simulation-service` | `default` | `agent-t-dev-simulation-service-irsa` | S3 artifact 읽기/쓰기, Secrets Manager 읽기 |
| `report-service` | `default` | `agent-t-dev-report-service-irsa` | S3 reports 쓰기, artifact 읽기 |
| `external-secrets` | `external-secrets-system` | `agent-t-dev-external-secrets-irsa` | Secrets Manager 읽기 |
| `aws-load-balancer-controller` | `kube-system` | `agent-t-dev-alb-controller-irsa` | ALB 생성/수정/삭제 |

### Helm Chart에서 사용

Helm values에 ServiceAccount annotation 추가:

```yaml
serviceAccount:
  create: true
  name: agent-service
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/agent-t-dev-agent-service-irsa
```

---

## EKS Add-ons

EKS 클러스터에 자동으로 설치되는 Add-ons:

| Add-on | 용도 |
|---|---|
| **vpc-cni** | Pod 네트워킹 (VPC IP 할당) |
| **coredns** | 클러스터 내 DNS |
| **kube-proxy** | Service 네트워크 라우팅 |
| **eks-pod-identity-agent** | Pod Identity (IRSA 후속 기능) |

Add-on 버전은 자동으로 최신 버전 선택. 특정 버전 고정이 필요하면 `cluster_addons` 변수 수정:

```hcl
cluster_addons = {
  vpc-cni = {
    version = "v1.16.0-eksbuild.1"
  }
  coredns = {
    version = "v1.11.1-eksbuild.4"
  }
}
```

---

## 노드 접근 (SSH)

Managed Node Group은 기본적으로 **SSH 키 없이 생성**된다.

노드에 접근이 필요한 경우:

### 1. SSM Session Manager (권장)

노드 IAM Role에 `AmazonSSMManagedInstanceCore` 정책이 연결되어 있으므로 SSM으로 접근 가능.

```bash
# 노드 인스턴스 ID 확인
aws ec2 describe-instances \
  --filters "Name=tag:eks:cluster-name,Values=agent-t-dev-eks" \
  --query "Reservations[*].Instances[*].[InstanceId,PrivateIpAddress,State.Name]" \
  --output table

# SSM Session 시작
aws ssm start-session --target i-0123456789abcdef0
```

### 2. SSH (선택사항)

SSH 접근이 필요하면 Node Group 생성 시 `remote_access` 블록 추가:

```hcl
resource "aws_eks_node_group" "this" {
  # ...

  remote_access {
    ec2_ssh_key = "my-keypair"
    source_security_group_ids = [aws_security_group.bastion.id]
  }
}
```

---

## 클러스터 모니터링

### CloudWatch Logs

EKS 컨트롤 플레인 로그는 자동으로 CloudWatch Logs로 전송된다 (선택적 활성화).

활성화 방법:
```hcl
resource "aws_eks_cluster" "this" {
  # ...

  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]
}
```

### Metrics Server

Pod/Node 메트릭 수집을 위해 Metrics Server 설치 필요 (6단계 Helm 구성에서 추가).

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 확인
kubectl top nodes
kubectl top pods -A
```

---

## 클러스터 업그레이드

EKS는 Kubernetes 버전을 자동으로 업그레이드하지 않는다. 수동 업그레이드 필요.

### 1. 컨트롤 플레인 업그레이드

```hcl
# infra/terraform/envs/dev/main.tf
module "eks" {
  # ...
  kubernetes_version = "1.31"  # 1.30 → 1.31
}
```

```bash
terraform plan
terraform apply
```

### 2. Node Group 업그레이드

Node Group은 컨트롤 플레인 업그레이드 후 별도로 업그레이드해야 한다.

**방법 1: Terraform으로 자동 업그레이드** (Rolling Update)
```bash
terraform apply  # Node Group이 자동으로 새 AMI로 교체
```

**방법 2: AWS Console/CLI로 수동 업그레이드**
```bash
aws eks update-nodegroup-version \
  --cluster-name agent-t-dev-eks \
  --nodegroup-name agent-t-dev-eks-general
```

### 3. Add-on 업그레이드

```bash
# 최신 Add-on 버전 확인
aws eks describe-addon-versions --addon-name vpc-cni --kubernetes-version 1.31

# Terraform에서 버전 업데이트 또는 null로 두면 자동 최신 버전 선택
```

---

## 문제 해결

### kubectl 접근 안 됨

**증상**:
```
error: You must be logged in to the server (Unauthorized)
```

**원인**: IAM 인증 정보가 없거나 권한이 부족.

**해결**:
1. AWS CLI 인증 확인
   ```bash
   aws sts get-caller-identity
   ```
2. kubeconfig 재생성
   ```bash
   aws eks update-kubeconfig --name agent-t-dev-eks
   ```
3. `aws-auth` ConfigMap에 IAM 사용자/역할 추가

### Pod가 AWS 리소스 접근 실패

**증상**:
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**원인**: IRSA 설정 누락.

**해결**:
1. ServiceAccount에 annotation 확인
   ```bash
   kubectl get sa agent-service -o yaml
   # annotations에 eks.amazonaws.com/role-arn 있어야 함
   ```
2. Pod에 환경 변수 주입 확인
   ```bash
   kubectl describe pod <pod-name>
   # AWS_ROLE_ARN, AWS_WEB_IDENTITY_TOKEN_FILE 환경 변수 있어야 함
   ```
3. IAM Role Trust Policy 확인
   ```bash
   aws iam get-role --role-name agent-t-dev-agent-service-irsa
   ```

### 노드가 Ready 상태 안 됨

**원인**: VPC Endpoint 미설정 (NAT Gateway off인 경우).

**해결**:
1. VPC Endpoint 확인 (ECR, S3, STS)
   ```bash
   aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<vpc-id>"
   ```
2. 노드 로그 확인 (SSM으로 접속)
   ```bash
   sudo journalctl -u kubelet
   ```

---

## 참고 문서

- [AWS EKS 문서](https://docs.aws.amazon.com/eks/)
- [kubectl 설치](https://kubernetes.io/docs/tasks/tools/)
- [eksctl (선택사항)](https://eksctl.io/)
- [IRSA 문서](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
