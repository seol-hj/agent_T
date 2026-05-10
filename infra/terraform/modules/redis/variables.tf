variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (Redis 식별자 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev / prod)."
}

variable "vpc_id" {
  type        = string
  description = "Redis를 배치할 VPC ID (security group 생성에 사용)."
}

variable "private_db_subnet_ids" {
  type        = list(string)
  description = "Redis를 배치할 private DB subnet IDs (intra subnet — NAT 미경유)."

  validation {
    condition     = length(var.private_db_subnet_ids) >= 2
    error_message = "Redis subnet group은 최소 2개의 서브넷이 필요하다."
  }
}

variable "allowed_security_group_ids" {
  type        = list(string)
  description = "Redis에 접근 가능한 security group IDs (일반적으로 EKS 노드 SG)."
  default     = []
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "Redis에 접근 가능한 CIDR 블록 목록 (EKS private-app subnet CIDR)."
  default     = []
}

variable "engine_version" {
  type        = string
  description = "Redis 엔진 버전."
  default     = "7.1"
}

variable "node_type" {
  type        = string
  description = "Redis 노드 타입 (dev: cache.t4g.micro, prod: cache.r7g.large 등)."

  validation {
    condition     = can(regex("^cache\\.", var.node_type))
    error_message = "node_type은 'cache.'로 시작해야 한다."
  }
}

variable "num_cache_clusters" {
  type        = number
  description = "캐시 클러스터 수 (1 = single node, 2+ = replica with failover)."
  default     = 1

  validation {
    condition     = var.num_cache_clusters >= 1 && var.num_cache_clusters <= 6
    error_message = "num_cache_clusters는 1~6 사이여야 한다."
  }
}

variable "multi_az_enabled" {
  type        = bool
  description = "Multi-AZ 배포 여부 (prod: true, dev: false 권장)."
  default     = false
}

variable "automatic_failover_enabled" {
  type        = bool
  description = "자동 failover 활성화 (num_cache_clusters >= 2 일 때만 가능)."
  default     = false
}

variable "at_rest_encryption_enabled" {
  type        = bool
  description = "저장 데이터 암호화 활성화."
  default     = true
}

variable "transit_encryption_enabled" {
  type        = bool
  description = "전송 중 암호화 활성화 (TLS)."
  default     = true
}

variable "auth_token_enabled" {
  type        = bool
  description = "Redis AUTH token 활성화 여부 (transit_encryption_enabled=true 필요)."
  default     = true
}

variable "auth_token_secret_arn" {
  type        = string
  description = "AUTH token을 저장할 Secrets Manager secret ARN (auth_token_enabled=true 시 필수)."
  default     = ""
}

variable "snapshot_retention_limit" {
  type        = number
  description = "자동 스냅샷 보존 기간 (일). 0이면 비활성화."
  default     = 5

  validation {
    condition     = var.snapshot_retention_limit >= 0 && var.snapshot_retention_limit <= 35
    error_message = "snapshot_retention_limit는 0~35 사이여야 한다."
  }
}

variable "snapshot_window" {
  type        = string
  description = "스냅샷 시간대 (UTC). 예: '03:00-05:00'."
  default     = "03:00-05:00"
}

variable "maintenance_window" {
  type        = string
  description = "유지보수 시간대 (UTC). 예: 'mon:05:00-mon:07:00'."
  default     = "mon:05:00-mon:07:00"
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
