variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (클러스터 이름 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev / prod)."
}

variable "vpc_id" {
  type        = string
  description = "EKS 클러스터를 배치할 VPC ID."
}

variable "private_app_subnet_ids" {
  type        = list(string)
  description = "EKS 노드를 배치할 private-app subnet IDs."

  validation {
    condition     = length(var.private_app_subnet_ids) >= 2
    error_message = "EKS는 최소 2개의 서브넷이 필요하다."
  }
}

variable "kubernetes_version" {
  type        = string
  description = "EKS Kubernetes 버전."
  default     = "1.30"
}

variable "cluster_endpoint_public_access" {
  type        = bool
  description = "클러스터 API 엔드포인트 public 접근 허용 여부 (dev: true, prod: false 권장)."
  default     = true
}

variable "cluster_endpoint_private_access" {
  type        = bool
  description = "클러스터 API 엔드포인트 private 접근 허용 여부 (항상 true 권장)."
  default     = true
}

variable "cluster_endpoint_public_access_cidrs" {
  type        = list(string)
  description = "Public 엔드포인트 접근 허용 CIDR 목록 (cluster_endpoint_public_access=true 일 때 적용)."
  default     = ["0.0.0.0/0"]
}

variable "node_groups" {
  type = map(object({
    instance_types = list(string)
    desired_size   = number
    min_size       = number
    max_size       = number
    disk_size      = optional(number, 50)
    capacity_type  = optional(string, "ON_DEMAND")
    taints = optional(list(object({
      key    = string
      value  = string
      effect = string
    })), [])
    labels = optional(map(string), {})
  }))
  description = "Managed Node Group 설정 (키는 node group 이름)."

  default = {
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
}

variable "cluster_addons" {
  type = map(object({
    version = optional(string, null)
  }))
  description = "EKS Add-ons 설정 (키는 add-on 이름). version null이면 최신 버전 자동 선택."
  default = {
    vpc-cni = {
      version = null
    }
    coredns = {
      version = null
    }
    kube-proxy = {
      version = null
    }
    eks-pod-identity-agent = {
      version = null
    }
  }
}

variable "enable_irsa" {
  type        = bool
  description = "IRSA (IAM Roles for Service Accounts) 활성화 여부 (OIDC provider 생성)."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
