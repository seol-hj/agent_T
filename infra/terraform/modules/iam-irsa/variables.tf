variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (IAM Role 이름 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev / prod)."
}

variable "oidc_provider_arn" {
  type        = string
  description = "EKS 클러스터 OIDC provider ARN (EKS 모듈 출력)."
}

variable "oidc_provider_url" {
  type        = string
  description = "EKS 클러스터 OIDC provider URL (https:// 제외, EKS 모듈 출력)."
}

variable "service_accounts" {
  type = map(object({
    namespace       = string
    service_account = string
    policy_arns     = optional(list(string), [])
    inline_policies = optional(map(string), {})
  }))
  description = <<-EOT
    서비스별 IRSA 설정.
    - key: IAM Role 이름 suffix (예: "agent-service")
    - namespace: Kubernetes namespace
    - service_account: ServiceAccount 이름
    - policy_arns: 연결할 관리형 또는 사용자 정의 IAM Policy ARN 목록
    - inline_policies: 인라인 정책 (map의 키는 정책 이름, 값은 JSON 문자열)
  EOT
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
