variable "project_name" {
  type        = string
  description = "프로젝트 식별자"
}

variable "env" {
  type        = string
  description = "환경 식별자 (dev | prod)"
}

variable "region" {
  type        = string
  description = "AWS 리전"
}

variable "tags" {
  type        = map(string)
  description = "공통 태그"
  default     = {}
}
