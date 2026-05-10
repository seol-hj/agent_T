# Terraform Module: EKS

EKS 클러스터 + Managed Node Group + OIDC Provider + Security Group 생성.

---

## 책임

- EKS 클러스터 생성 (Kubernetes 1.30)
- Managed Node Group 생성 (private-app subnet 배치)
- OIDC provider 생성 (IRSA 활성화)
- Security Group 생성 (컨트롤 플레인 ↔ 노드 통신)
- EKS Add-ons 설치 (vpc-cni, coredns, kube-proxy, eks-pod-identity-agent)
- IAM Role 생성 (클러스터, 노드)

---

## 입력 변수

| 변수 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `project_name` | string | ✅ | - | 프로젝트 식별자 |
| `env` | string | ✅ | - | 환경 (dev / prod) |
| `vpc_id` | string | ✅ | - | VPC ID |
| `private_app_subnet_ids` | list(string) | ✅ | - | private-app subnet IDs (최소 2개) |
| `kubernetes_version` | string | | `"1.30"` | Kubernetes 버전 |
| `cluster_endpoint_public_access` | bool | | `true` | Public 엔드포인트 활성화 |
| `cluster_endpoint_private_access` | bool | | `true` | Private 엔드포인트 활성화 |
| `cluster_endpoint_public_access_cidrs` | list(string) | | `["0.0.0.0/0"]` | Public 접근 허용 CIDR |
| `node_groups` | map(object) | | `{ general = {...} }` | Node Group 설정 |
| `cluster_addons` | map(object) | | `{ vpc-cni = {...}, ... }` | EKS Add-ons 설정 |
| `enable_irsa` | bool | | `true` | IRSA (OIDC provider) 활성화 |
| `tags` | map(string) | | `{}` | 공통 태그 |

---

## 출력

| 출력 | 설명 |
|---|---|
| `cluster_name` | EKS 클러스터 이름 |
| `cluster_id` | EKS 클러스터 ID |
| `cluster_arn` | EKS 클러스터 ARN |
| `cluster_endpoint` | API 엔드포인트 (kubectl 접근) |
| `cluster_certificate_authority_data` | CA 인증서 (base64) |
| `cluster_version` | Kubernetes 버전 |
| `cluster_security_group_id` | 클러스터 security group ID |
| `node_security_group_id` | 노드 security group ID (RDS/Redis 접근 허용) |
| `cluster_oidc_issuer_url` | OIDC provider URL (IRSA) |
| `oidc_provider_arn` | OIDC provider ARN (IRSA Trust Policy) |
| `node_group_names` | Node Group 이름 목록 |
| `node_group_arns` | Node Group ARN 목록 |
| `node_role_arn` | 노드 IAM Role ARN |

---

## 사용 예시

```hcl
module "eks" {
  source = "../../modules/eks"

  project_name           = var.project_name
  env                    = var.env
  vpc_id                 = module.vpc.vpc_id
  private_app_subnet_ids = module.vpc.private_app_subnet_ids

  kubernetes_version                   = "1.30"
  cluster_endpoint_public_access       = true
  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]

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

  cluster_addons = {
    vpc-cni = { version = null }
    coredns = { version = null }
    kube-proxy = { version = null }
    eks-pod-identity-agent = { version = null }
  }

  enable_irsa = true

  tags = local.common_tags
}
```

---

## Node Group 설정 (prod 예시)

```hcl
node_groups = {
  general = {
    instance_types = ["m5.large"]
    desired_size   = 3
    min_size       = 2
    max_size       = 6
    disk_size      = 100
    capacity_type  = "ON_DEMAND"
    labels = {
      workload = "general"
    }
  }
  sumo-compute = {
    instance_types = ["c5.2xlarge"]
    desired_size   = 1
    min_size       = 0
    max_size       = 5
    disk_size      = 200
    capacity_type  = "SPOT"
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

---

## kubeconfig 설정

```bash
aws eks update-kubeconfig \
  --name agent-t-dev-eks \
  --region ap-northeast-2 \
  --alias agent-t-dev

kubectl cluster-info
kubectl get nodes
```

---

## IRSA (IAM Roles for Service Accounts)

OIDC provider가 자동으로 생성되어 ServiceAccount ↔ IAM Role 연결이 가능하다.

자세한 내용은 [`docs/eks.md`](../../../../docs/eks.md) 참조.

---

## 참고

- Kubernetes 버전: 1.30
- 노드 OS: Amazon Linux 2
- Security Group: 컨트롤 플레인 ↔ 노드 통신 자동 구성
- SSM Agent: 노드 접근용 (ssh 불필요)
