variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (DB 식별자 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev / prod)."
}

variable "vpc_id" {
  type        = string
  description = "RDS를 배치할 VPC ID (security group 생성에 사용)."
}

variable "private_db_subnet_ids" {
  type        = list(string)
  description = "RDS를 배치할 private DB subnet IDs (intra subnet — NAT 미경유)."

  validation {
    condition     = length(var.private_db_subnet_ids) >= 2
    error_message = "RDS subnet group은 최소 2개의 서브넷이 필요하다."
  }
}

variable "allowed_security_group_ids" {
  type        = list(string)
  description = "RDS에 접근 가능한 security group IDs (일반적으로 EKS 노드 SG)."
  default     = []
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "RDS에 접근 가능한 CIDR 블록 목록 (EKS private-app subnet CIDR)."
  default     = []
}

variable "engine_version" {
  type        = string
  description = "PostgreSQL 엔진 버전."
  default     = "16.13"
}

variable "instance_class" {
  type        = string
  description = "RDS 인스턴스 타입 (dev: db.t4g.micro, prod: db.r7g.large 등)."

  validation {
    condition     = can(regex("^db\\.", var.instance_class))
    error_message = "instance_class는 'db.'로 시작해야 한다."
  }
}

variable "allocated_storage" {
  type        = number
  description = "할당할 스토리지 크기 (GB)."
  default     = 20

  validation {
    condition     = var.allocated_storage >= 20
    error_message = "allocated_storage는 최소 20GB 이상이어야 한다."
  }
}

variable "max_allocated_storage" {
  type        = number
  description = "Auto-scaling 최대 스토리지 크기 (GB). 0이면 비활성화."
  default     = 100
}

variable "db_name" {
  type        = string
  description = "초기 생성할 데이터베이스 이름."
  default     = "agent_t"
}

variable "master_username" {
  type        = string
  description = "마스터 사용자 이름."
  default     = "agent_t_admin"
}

variable "multi_az" {
  type        = bool
  description = "Multi-AZ 배포 여부 (prod: true, dev: false 권장)."
  default     = false
}

variable "backup_retention_days" {
  type        = number
  description = "자동 백업 보존 기간 (일). 0이면 백업 비활성화."
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 0 && var.backup_retention_days <= 35
    error_message = "backup_retention_days는 0~35 사이여야 한다."
  }
}

variable "backup_window" {
  type        = string
  description = "백업 시간대 (UTC). 예: '03:00-04:00'."
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  type        = string
  description = "유지보수 시간대 (UTC). 예: 'mon:04:00-mon:05:00'."
  default     = "mon:04:00-mon:05:00"
}

variable "deletion_protection" {
  type        = bool
  description = "삭제 보호 (prod: true, dev: false 권장)."
  default     = false
}

variable "skip_final_snapshot" {
  type        = bool
  description = "삭제 시 최종 스냅샷 건너뛰기 (dev: true, prod: false 권장)."
  default     = true
}

variable "db_secret_arn" {
  type        = string
  description = "RDS 인증 정보를 저장할 Secrets Manager secret ARN (secrets-manager 모듈 출력)."
}

variable "tags" {
  type        = map(string)
  description = "공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
