variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (리소스명 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev | prod)."
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR. /16 권장 (subnet 자동 도출이 /20 으로 떨어지도록 설계)."

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr 는 유효한 CIDR 표기여야 한다 (예: 10.10.0.0/16)."
  }
}

variable "azs" {
  type        = list(string)
  description = "VPC 를 펼칠 가용영역 목록 (각 tier 의 subnet 수와 동일)."

  validation {
    condition     = length(var.azs) >= 2
    error_message = "AZ 는 최소 2개 이상이어야 한다."
  }

  validation {
    condition     = length(var.azs) <= 4
    error_message = "본 모듈의 CIDR 자동 도출은 AZ 4개까지 지원한다 (newbits=4 기준). 더 많이 필요하면 *_subnet_cidrs 로 override 하라."
  }
}

variable "enable_nat_gateway" {
  type        = bool
  description = "NAT Gateway 생성 여부. false 면 private-app 서브넷에는 인터넷 라우트가 없다 (VPC Endpoint 로만 외부 통신)."
  default     = false
}

variable "single_nat_gateway" {
  type        = bool
  description = "true: 모든 AZ 가 단일 NAT 공유 (비용↓, HA↓ — dev 권장). false: AZ별 NAT (HA↑ — prod 권장)."
  default     = true
}

# ============================================================================
# CIDR override — 비워두면 vpc_cidr 으로부터 자동 도출.
# 자동 도출 로직 (newbits = 4 → /20):
#   public[i]      = cidrsubnet(vpc_cidr, 4, i)
#   private_app[i] = cidrsubnet(vpc_cidr, 4, i + 4)
#   private_db[i]  = cidrsubnet(vpc_cidr, 4, i + 8)
# 예) 10.10.0.0/16, AZ 3개 →
#   public      : 10.10.0.0/20,  10.10.16.0/20, 10.10.32.0/20
#   private-app : 10.10.64.0/20, 10.10.80.0/20, 10.10.96.0/20
#   private-db  : 10.10.128.0/20,10.10.144.0/20,10.10.160.0/20
# ============================================================================

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "Public subnet CIDR override. 빈 list 면 자동 도출."
  default     = []
}

variable "private_app_subnet_cidrs" {
  type        = list(string)
  description = "Private-app subnet CIDR override."
  default     = []
}

variable "private_db_subnet_cidrs" {
  type        = list(string)
  description = "Private-db subnet CIDR override."
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "리소스에 적용할 공통 태그 (env 단의 common_tags 를 기대 — project/env/managed_by 포함)."
  default     = {}
}
