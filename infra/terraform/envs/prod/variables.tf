variable "project_name" {
  type        = string
  description = "프로젝트 식별자. 모든 리소스 이름 prefix 로 사용된다."
  default     = "agent-t"
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev | prod)."
  default     = "prod"

  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "env 는 'dev' 또는 'prod' 만 허용된다."
  }
}

variable "region" {
  type        = string
  description = "AWS 리전."
  default     = "ap-northeast-2"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR. dev/prod 간 충돌이 없도록 분리한다."
  default     = "10.20.0.0/16"
}

variable "azs" {
  type        = list(string)
  description = "VPC 를 펼칠 가용영역 목록. prod 는 3개를 권장."
  default     = ["ap-northeast-2a", "ap-northeast-2b", "ap-northeast-2c"]

  validation {
    condition     = length(var.azs) >= 2
    error_message = "AZ 는 최소 2개 이상이어야 한다 (prod 는 3개 권장)."
  }
}

variable "tags" {
  type        = map(string)
  description = "공통 태그에 추가로 병합할 사용자 태그."
  default     = {}
}

variable "enable_nat_gateway" {
  type        = bool
  description = "NAT Gateway 생성 여부. prod 는 기본 true (워크로드 외부 통신 보장)."
  default     = true
}

variable "single_nat_gateway" {
  type        = bool
  description = "true: AZ 공통 단일 NAT (HA↓). prod 는 false 권장 (AZ 별 NAT)."
  default     = false
}

# ============================================================================
# VPC Endpoints 토글 — prod 는 보안/비용 모두 endpoint 권장.
# ============================================================================
variable "enable_bedrock_endpoint" {
  type        = bool
  description = "Bedrock(+Runtime) endpoint 생성 여부."
  default     = true
}

variable "enable_kms_endpoint" {
  type        = bool
  description = "KMS endpoint 생성 여부."
  default     = true
}

variable "enable_cloudwatch_endpoint" {
  type        = bool
  description = "CloudWatch Logs endpoint 생성 여부."
  default     = true
}

# ============================================================================
# S3 lifecycle — 버킷 키별 정책 (artifact / rag_source / reports / model_data)
# ============================================================================
variable "s3_lifecycle_rules" {
  type = map(object({
    enabled                            = optional(bool, false)
    expiration_days                    = optional(number, null)
    noncurrent_version_expiration_days = optional(number, null)
    abort_incomplete_multipart_days    = optional(number, 7)
  }))
  description = "S3 버킷별 lifecycle 정책. 자세한 의미는 modules/s3/variables.tf 참조."
  default     = {}
}

# ============================================================================
# ECR
# ============================================================================
variable "ecr_image_tag_mutability" {
  type        = string
  description = "ECR 태그 변경 가능성. prod 는 IMMUTABLE 표준."
  default     = "IMMUTABLE"

  validation {
    condition     = contains(["IMMUTABLE", "MUTABLE"], var.ecr_image_tag_mutability)
    error_message = "ecr_image_tag_mutability 는 'IMMUTABLE' 또는 'MUTABLE' 만 허용된다."
  }
}
