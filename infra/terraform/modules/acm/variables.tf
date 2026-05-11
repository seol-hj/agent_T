variable "project_name" {
  type        = string
  description = "프로젝트 식별자"
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev | prod)"
}

variable "domain_name" {
  type        = string
  description = "메인 도메인 이름 (예: seolphung.com)"
}

variable "subject_alternative_names" {
  type        = list(string)
  description = "추가 도메인 목록 (와일드카드 포함 가능)"
  default     = []

  # 예: ["*.seolphung.com", "api.seolphung.com", "argocd.seolphung.com"]
}

variable "route53_zone_id" {
  type        = string
  description = "Route 53 Hosted Zone ID (DNS 검증용)"
  default     = ""
}

variable "enable_dns_validation" {
  type        = bool
  description = "DNS 자동 검증 활성화 (Route 53 사용 시)"
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "공통 태그"
  default     = {}
}
