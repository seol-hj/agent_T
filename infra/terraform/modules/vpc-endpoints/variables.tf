variable "project_name" {
  type        = string
  description = "프로젝트 식별자 (리소스명 prefix)."
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev | prod)."
}

variable "region" {
  type        = string
  description = "AWS 리전. interface endpoint service name 자동 도출에 사용."
}

variable "vpc_id" {
  type        = string
  description = "Endpoint 가 attach 될 VPC ID (vpc 모듈 output)."
}

variable "vpc_cidr_block" {
  type        = string
  description = "Endpoint SG 의 ingress source CIDR (보통 vpc 모듈의 vpc_cidr_block)."
}

variable "private_app_subnet_ids" {
  type        = list(string)
  description = "Interface endpoint ENI 가 배치될 subnet 목록. AZ 개수만큼 1:1 ENI 생성."
}

variable "private_route_table_ids" {
  type        = list(string)
  description = "S3 Gateway endpoint 가 prefix-list 라우트를 추가할 route table 목록 (보통 private-app + private-db 전체)."
}

# ============================================================================
# Endpoint on/off 토글
# ============================================================================
variable "enable_bedrock_endpoint" {
  type        = bool
  description = "Bedrock + Bedrock Runtime endpoint 생성 여부. 리전이 Bedrock 미지원이면 false."
  default     = true
}

variable "enable_kms_endpoint" {
  type        = bool
  description = "KMS endpoint 생성 여부 (Secrets Manager / RDS 암호화 호출에 유용)."
  default     = true
}

variable "enable_cloudwatch_endpoint" {
  type        = bool
  description = "CloudWatch Logs endpoint 생성 여부 (EKS 컨테이너 로그 수집 시 필수)."
  default     = true
}

# ============================================================================
# Bedrock service name override (리전별 가용성 / 신규 서비스명 변경 대응)
# 빈 문자열이면 com.amazonaws.<region>.<service> 로 자동 도출.
# ============================================================================
variable "bedrock_runtime_service_name" {
  type        = string
  description = "Bedrock Runtime endpoint service name override."
  default     = ""
}

variable "bedrock_service_name" {
  type        = string
  description = "Bedrock control plane endpoint service name override."
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "리소스에 적용할 공통 태그 (env 단의 common_tags 전달)."
  default     = {}
}
