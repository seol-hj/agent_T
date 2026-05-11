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
  description = "관리할 도메인 이름 (예: seolphung.com)"
}

variable "alb_dns_name" {
  type        = string
  description = "ALB DNS 이름 (Ingress에서 가져옴)"
  default     = ""
}

variable "alb_zone_id" {
  type        = string
  description = "ALB Zone ID"
  default     = ""
}

variable "alb_subdomains" {
  type = map(object({
    subdomain = string
  }))
  description = "ALB와 연결할 서브도메인 목록"
  default     = {}
}

variable "tags" {
  type        = map(string)
  description = "공통 태그"
  default     = {}
}
