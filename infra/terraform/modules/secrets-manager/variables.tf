variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (시크릿 이름 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev / prod)."
}

variable "kms_key_arn" {
  type        = string
  description = "시크릿 암호화에 사용할 KMS Key ARN. 빈 문자열이면 AWS 관리형 키 사용."
  default     = ""
}

variable "recovery_window_in_days" {
  type        = number
  description = "시크릿 삭제 후 복구 가능 기간 (일). 7~30 권장."
  default     = 30

  validation {
    condition     = var.recovery_window_in_days >= 7 && var.recovery_window_in_days <= 30
    error_message = "recovery_window_in_days 는 7~30일 사이여야 한다."
  }
}

variable "create_redis_auth_secret" {
  type        = bool
  description = "Redis auth token secret 생성 여부 (Redis auth 사용 시 true)."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
