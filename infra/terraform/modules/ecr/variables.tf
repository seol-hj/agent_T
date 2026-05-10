variable "project_name" {
  type        = string
  description = "프로젝트 식별자. 레포 namespace 의 prefix."
}

variable "env" {
  type        = string
  description = "환경 식별자. 레포 namespace 의 두 번째 토큰."
}

variable "repositories" {
  type        = list(string)
  description = "생성할 ECR 레포지토리 이름 목록 (namespace 뒤에 붙음)."
  default = [
    "frontend",
    "api-service",
    "agent-service",
    "simulation-service",
    "analysis-service",
    "report-service",
    "simulation-runner",
  ]

  validation {
    condition     = length(var.repositories) > 0
    error_message = "repositories 는 최소 1개 이상이어야 한다."
  }
}

variable "image_tag_mutability" {
  type        = string
  description = "IMMUTABLE: 동일 태그 재푸시 금지 (운영 권장). MUTABLE: 재푸시 허용 (개발 편의)."
  default     = "IMMUTABLE"

  validation {
    condition     = contains(["IMMUTABLE", "MUTABLE"], var.image_tag_mutability)
    error_message = "image_tag_mutability 는 'IMMUTABLE' 또는 'MUTABLE' 만 허용된다."
  }
}

variable "scan_on_push" {
  type        = bool
  description = "ECR Basic Scanning (push 시 자동) 활성화."
  default     = true
}

variable "kms_key_arn" {
  type        = string
  description = "KMS Key ARN (지정 시 SSE-KMS 사용). 빈 문자열이면 AES256."
  default     = ""
}

# ============================================================================
# Lifecycle 변수
# ============================================================================
variable "untagged_image_expiration_days" {
  type        = number
  description = "Untagged 이미지가 push 된 지 N 일 후 자동 expire."
  default     = 14
}

variable "tagged_image_retention_count" {
  type        = number
  description = "tag_prefix_filters 매칭 태그 중 최근 N 개만 유지. 0 이면 룰 비활성."
  default     = 30
}

variable "tag_prefix_filters" {
  type        = list(string)
  description = "유지/정리 룰의 태그 prefix 필터 (이 prefix 가 아닌 태그는 영구 보존)."
  default     = ["sha-"]
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
