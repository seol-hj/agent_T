variable "project_name" {
  type        = string
  description = "프로젝트 식별자."
}

variable "env" {
  type        = string
  description = "환경 식별자."
}

variable "namespace" {
  type        = string
  description = "Argo CD 가 설치될 namespace."
  default     = "argocd"
}

variable "helm_chart_version" {
  type        = string
  description = "argo-cd Helm chart 버전 (latest 금지, 명시적 핀)."
  default     = "7.6.12"
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (kubernetes 리소스에는 label 로 변환)."
  default     = {}
}

# === 5단계에서 추가될 인풋 ===
# variable "cluster_name" { type = string }
# variable "values_overrides" { type = any  default = {} }
