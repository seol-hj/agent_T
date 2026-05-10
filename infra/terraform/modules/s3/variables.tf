variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (버킷 이름 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev | prod)."
}

variable "kms_key_arn" {
  type        = string
  description = "SSE-KMS 사용 시 KMS Key ARN. 빈 문자열이면 SSE-S3 (AES256)."
  default     = ""
}

variable "enforce_tls" {
  type        = bool
  description = "true 면 모든 버킷에 aws:SecureTransport=false 거부 정책을 적용한다."
  default     = true
}

variable "lifecycle_rules" {
  type = map(object({
    enabled                            = optional(bool, false)
    expiration_days                    = optional(number, null)
    noncurrent_version_expiration_days = optional(number, null)
    abort_incomplete_multipart_days    = optional(number, 7)
  }))
  description = <<-EOT
    버킷 키별 lifecycle 정책. 미지정/enabled=false 인 버킷은 lifecycle 미적용.
    유효 키: artifact / rag_source / reports / model_data.
    - expiration_days                    : 현재 객체 expiration (null = 미적용)
    - noncurrent_version_expiration_days : versioning 으로 남은 과거 버전 expiration
    - abort_incomplete_multipart_days    : 미완료 multipart 업로드 정리 기한 (default 7)
  EOT
  default     = {}

  validation {
    condition = alltrue([
      for k in keys(var.lifecycle_rules) :
      contains(["artifact", "rag_source", "reports", "model_data"], k)
    ])
    error_message = "lifecycle_rules 의 키는 artifact / rag_source / reports / model_data 만 허용된다."
  }
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
