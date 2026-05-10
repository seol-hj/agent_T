variable "project_name" {
  type        = string
  description = "프로젝트 식별자."
}

variable "env" {
  type        = string
  description = "환경 식별자."
}

variable "region" {
  type        = string
  description = "AWS 리전 (controller 의 --aws-region 인자에 사용)."
}

variable "namespace" {
  type        = string
  description = "controller 가 설치될 namespace."
  default     = "kube-system"
}

variable "service_account_name" {
  type        = string
  description = "controller ServiceAccount 이름 (공식 권장값)."
  default     = "aws-load-balancer-controller"
}

variable "helm_chart_version" {
  type        = string
  description = "aws-load-balancer-controller Helm chart 버전 (latest 금지)."
  default     = "1.8.1"
}

variable "tags" {
  type        = map(string)
  description = "공통 태그."
  default     = {}
}

# === 5단계에서 추가될 인풋 ===
# variable "cluster_name"       { type = string }
# variable "oidc_provider_arn"  { type = string }
# variable "oidc_provider_url"  { type = string }
# variable "vpc_id"             { type = string }
