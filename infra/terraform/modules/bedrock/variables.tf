variable "project_name" {
  type        = string
  description = "프로젝트 식별자."
}

variable "env" {
  type        = string
  description = "환경 식별자."
}

variable "allowed_model_ids" {
  type        = list(string)
  description = "호출 허용 모델 ID 목록 (IAM 정책의 Resource ARN 패턴으로 변환)."
  default = [
    # 예: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    #     "anthropic.claude-3-haiku-20240307-v1:0",
  ]
}

variable "tags" {
  type        = map(string)
  description = "공통 태그."
  default     = {}
}
