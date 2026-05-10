variable "project_name" {
  type        = string
  description = "프로젝트 식별자. 모든 리소스 이름 prefix 로 사용된다."
  default     = "agent-t"
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev | prod)."
  default     = "dev"

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
  default     = "10.10.0.0/16"
}

variable "azs" {
  type        = list(string)
  description = "VPC 를 펼칠 가용영역 목록. dev 는 2개를 권장."
  default     = ["ap-northeast-2a", "ap-northeast-2c"]

  validation {
    condition     = length(var.azs) >= 2
    error_message = "AZ 는 최소 2개 이상이어야 한다."
  }
}

variable "tags" {
  type        = map(string)
  description = "공통 태그에 추가로 병합할 사용자 태그."
  default     = {}
}

variable "enable_nat_gateway" {
  type        = bool
  description = "NAT Gateway 생성 여부. dev 는 비용 절감을 위해 기본 false (필요 시 tfvars 에서 true)."
  default     = false
}

variable "single_nat_gateway" {
  type        = bool
  description = "true: AZ 공통 단일 NAT (비용↓, HA↓). dev 는 true 권장."
  default     = true
}

# ============================================================================
# VPC Endpoints 토글 — NAT off 모드에서는 사실상 모두 필요하다.
# ============================================================================
variable "enable_bedrock_endpoint" {
  type        = bool
  description = "Bedrock(+Runtime) endpoint 생성 여부. 리전이 Bedrock 미지원이면 false."
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
  description = "ECR 태그 변경 가능성. dev 는 MUTABLE 권장 (재시도/디버깅 편의), prod 는 IMMUTABLE."
  default     = "IMMUTABLE"

  validation {
    condition     = contains(["IMMUTABLE", "MUTABLE"], var.ecr_image_tag_mutability)
    error_message = "ecr_image_tag_mutability 는 'IMMUTABLE' 또는 'MUTABLE' 만 허용된다."
  }
}
